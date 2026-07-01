"""Face2MBTI - FastAPI Web 服务入口"""

import base64
import logging
import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.config import settings
from app.workflow.graph import graph
from app.workflow.video_graph import video_graph
from app.utils.video_processor import extract_frames
from app.task_manager import create_task, update_task, get_task, run_task_async, TaskStatus, init_result_dir

# 路径常量
STATIC_DIR = Path(__file__).parent / "static"
UPLOAD_DIR = Path(settings.UPLOAD_DIR).resolve()
LOG_DIR = Path(settings.LOG_DIR).resolve()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时创建必要目录"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # 初始化结果持久化目录
    init_result_dir(settings.RESULT_DIR)
    # 配置按日期记录的日志文件
    _setup_date_logger()
    logger.info(f"上传目录: {UPLOAD_DIR}")
    logger.info(f"日志目录: {LOG_DIR}")
    yield


def _setup_date_logger():
    """配置按日期记录的日志，所有日志写入同一文件"""
    today = date.today().isoformat()  # e.g. 2026-07-01
    log_file = LOG_DIR / f"{today}.log"
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    # 将文件 handler 添加到 root logger
    root = logging.getLogger()
    root.addHandler(file_handler)
    logger.info(f"日志文件: {log_file}")


# 配置日志（控制台）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="Face2MBTI", description="看脸测 MBTI 性格分析", lifespan=lifespan)


@app.get("/")
async def index():
    """返回前端页面"""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/video")
async def video_page():
    """返回视频分析页面"""
    return FileResponse(STATIC_DIR / "video.html")


@app.get("/result")
async def result_page():
    """返回任务结果展示页"""
    return FileResponse(STATIC_DIR / "result.html")


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """接收上传的图片，保存文件后创建异步任务，立即返回 task_id

    Args:
        file: 上传的图片文件（支持 jpg/png/webp）

    Returns:
        {task_id, poll_interval}
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件")

    # 限制文件大小 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片文件过大，请上传小于 10MB 的图片")

    # 生成任务ID
    task_id = create_task()

    # 保存上传文件
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    save_path = task_dir / f"photo.{ext}"
    save_path.write_bytes(contents)
    media_url = f"/uploads/{task_id}/photo.{ext}"

    # 更新任务的媒体URL
    update_task(task_id, media_url=media_url)

    # 转为 base64 供工作流使用
    image_base64 = base64.b64encode(contents).decode("utf-8")

    # 包装工作流调用
    def run_workflow(input_data):
        logger.info(f"[{task_id}] 开始图片分析工作流")
        result = graph.invoke(input_data)
        logger.info(f"[{task_id}] 工作流完成: {result.get('result', {}).get('mbti_type', 'unknown')}")
        return result

    # 后台异步执行
    await run_task_async(task_id, run_workflow, {"image_base64": image_base64})

    return {"task_id": task_id, "poll_interval": settings.POLL_INTERVAL_SEC}


@app.post("/api/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """接收上传的视频，保存文件后创建异步任务，立即返回 task_id

    Args:
        file: 上传的视频文件（支持 mp4/webm/mov 等）

    Returns:
        {task_id, poll_interval}
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="请上传有效的视频文件")

    # 限制文件大小
    max_size = settings.VIDEO_MAX_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"视频文件过大，请上传小于 {settings.VIDEO_MAX_SIZE_MB}MB 的视频",
        )

    # 生成任务ID
    task_id = create_task()

    # 保存上传文件
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "mp4"
    save_path = task_dir / f"video.{ext}"
    save_path.write_bytes(contents)
    media_url = f"/uploads/{task_id}/video.{ext}"

    # 更新任务的媒体URL
    update_task(task_id, media_url=media_url)

    # 包装工作流调用（含抽帧）
    def run_workflow(video_bytes):
        logger.info(f"[{task_id}] 开始视频抽帧")
        frames_base64, timestamps = extract_frames(video_bytes, interval=settings.FRAME_INTERVAL_SEC)
        if not frames_base64:
            raise RuntimeError("未能从视频中抽取有效帧")
        logger.info(f"[{task_id}] 抽取 {len(frames_base64)} 帧，开始视频分析工作流")
        result = video_graph.invoke({
            "frames_base64": frames_base64,
            "frame_timestamps": timestamps,
            "is_video_input": True,
        })
        logger.info(f"[{task_id}] 工作流完成: {result.get('result', {}).get('mbti_type', 'unknown')}")
        return result

    # 后台异步执行
    await run_task_async(task_id, run_workflow, contents)

    return {"task_id": task_id, "poll_interval": settings.POLL_INTERVAL_SEC}


@app.get("/api/task/{task_id}")
async def query_task(task_id: str):
    """查询任务状态和结果

    Returns:
        {status, result?, error?, media_url?}
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    response_data = {
        "status": task["status"].value,
        "media_url": task.get("media_url"),
    }

    if task["status"] == TaskStatus.COMPLETED:
        response_data["result"] = task.get("result")
    elif task["status"] == TaskStatus.FAILED:
        response_data["error"] = task.get("error", "未知错误")

    return JSONResponse(
        content=response_data,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# 挂载上传文件目录（供前端访问上传的照片/视频）
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 挂载静态文件（CSS、JS 等）
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
