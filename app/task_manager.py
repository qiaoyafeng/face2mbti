"""异步任务管理模块

职责: 管理测评任务的生命周期，支持后台异步执行 LangGraph 工作流。
任务结果持久化到文件，支持按 task_id 查询。
"""

import asyncio
import json
import logging
import threading
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# 全局任务存储与线程锁（内存缓存）
_tasks: dict[str, dict] = {}
_lock = threading.Lock()

# 结果持久化目录，由 init_result_dir() 设置
_result_dir: Optional[Path] = None


def init_result_dir(result_dir: str):
    """初始化结果持久化目录"""
    global _result_dir
    _result_dir = Path(result_dir).resolve()
    _result_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"结果存储目录: {_result_dir}")


def _save_result_to_file(task_id: str, task_data: dict):
    """将任务结果持久化到 JSON 文件"""
    if _result_dir is None:
        return
    result_file = _result_dir / f"{task_id}.json"
    data_to_save = {
        "task_id": task_id,
        "status": task_data["status"].value if isinstance(task_data["status"], TaskStatus) else task_data["status"],
        "result": task_data.get("result"),
        "error": task_data.get("error"),
        "media_url": task_data.get("media_url"),
        "created_at": task_data.get("created_at"),
        "updated_at": datetime.now().isoformat(),
    }
    result_file.write_text(json.dumps(data_to_save, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_result_from_file(task_id: str) -> Optional[dict]:
    """从 JSON 文件加载任务结果"""
    if _result_dir is None:
        return None
    result_file = _result_dir / f"{task_id}.json"
    if not result_file.exists():
        return None
    try:
        data = json.loads(result_file.read_text(encoding="utf-8"))
        # 将 status 字符串转回枚举
        status_str = data.get("status", "PENDING")
        data["status"] = TaskStatus(status_str)
        return data
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"读取任务结果文件失败: {task_id} - {e}")
        return None


def create_task(media_url: Optional[str] = None) -> str:
    """创建新任务，返回 task_id"""
    task_id = uuid.uuid4().hex[:12]
    with _lock:
        _tasks[task_id] = {
            "status": TaskStatus.PENDING,
            "result": None,
            "error": None,
            "media_url": media_url,
            "created_at": datetime.now().isoformat(),
        }
    logger.info(f"任务已创建: {task_id}")
    return task_id


def update_task(task_id: str, **kwargs):
    """更新任务状态/结果，终态时持久化到文件"""
    with _lock:
        if task_id in _tasks:
            _tasks[task_id].update(kwargs)
            status = kwargs.get("status")
            # 任务到达终态时持久化
            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                _save_result_to_file(task_id, _tasks[task_id])


def get_task(task_id: str) -> Optional[dict]:
    """获取任务信息（返回快照副本）

    优先从内存缓存查找，找不到则从持久化文件加载。
    """
    with _lock:
        task = _tasks.get(task_id)
        if task:
            return dict(task)

    # 内存中没有，尝试从文件加载
    file_task = _load_result_from_file(task_id)
    if file_task:
        # 回填到内存缓存
        with _lock:
            _tasks[task_id] = file_task
        return file_task

    return None


async def run_task_async(task_id: str, func, *args, **kwargs):
    """在后台线程中异步执行同步工作流函数

    Args:
        task_id: 任务ID
        func: 同步工作流函数（如 graph.invoke）
        *args, **kwargs: 传递给 func 的参数
    """

    def _run():
        update_task(task_id, status=TaskStatus.PROCESSING)
        try:
            result = func(*args, **kwargs)
            final_result = result.get("result")
            state_error = result.get("error")  # 检查 state 级别的 error
            if final_result and not final_result.get("error") and not state_error:
                # 一次性写入 status + result，避免中间状态被读取
                update_task(task_id, status=TaskStatus.COMPLETED, result=final_result)
                logger.info(f"任务完成: {task_id}")
            else:
                error_msg = (
                    final_result.get("message", "分析未返回结果") if (final_result and final_result.get("error"))
                    else state_error if state_error
                    else "分析未返回结果"
                )
                update_task(task_id, status=TaskStatus.FAILED, error=error_msg)
                logger.warning(f"任务失败: {task_id} - {error_msg}")
        except Exception as e:
            update_task(task_id, status=TaskStatus.FAILED, error=str(e))
            logger.error(f"任务异常: {task_id} - {e}", exc_info=True)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run)
