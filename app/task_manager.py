"""异步任务管理模块

职责: 管理测评任务的生命周期，支持后台异步执行 LangGraph 工作流。
"""

import asyncio
import logging
import threading
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# 全局任务存储与线程锁
_tasks: dict[str, dict] = {}
_lock = threading.Lock()


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
    """更新任务状态/结果"""
    with _lock:
        if task_id in _tasks:
            _tasks[task_id].update(kwargs)


def get_task(task_id: str) -> Optional[dict]:
    """获取任务信息（返回快照副本）"""
    with _lock:
        task = _tasks.get(task_id)
        if task:
            return dict(task)
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
