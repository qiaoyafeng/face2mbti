"""视频处理工具模块

职责: 从上传的视频中抽取关键帧，转换为 base64 图片列表
"""

import base64
import logging
import os
import tempfile
from pathlib import Path

import ffmpeg

logger = logging.getLogger(__name__)


def get_video_duration(video_path: str) -> float:
    """获取视频时长（秒）

    Args:
        video_path: 视频文件路径

    Returns:
        视频时长（秒）
    """
    probe = ffmpeg.probe(video_path)
    duration = float(probe["format"]["duration"])
    return duration


def extract_frames(video_bytes: bytes, interval: float = 5.0) -> tuple[list[str], list[float]]:
    """从视频中按指定间隔抽取关键帧，返回 base64 编码的图片列表和对应时间戳

    Args:
        video_bytes: 视频文件的二进制内容
        interval: 抽帧间隔（秒）

    Returns:
        (帧图片 base64 列表, 对应时间戳列表)
    """
    tmp_dir = None
    try:
        # 创建临时目录
        tmp_dir = tempfile.mkdtemp(prefix="face2mbti_video_")
        video_path = os.path.join(tmp_dir, "input.mp4")

        # 写入临时视频文件
        with open(video_path, "wb") as f:
            f.write(video_bytes)

        # 获取视频时长
        duration = get_video_duration(video_path)
        logger.info(f"视频时长: {duration:.1f}s, 抽帧间隔: {interval}s")

        # 计算需要抽取的帧数
        num_frames = max(1, int(duration / interval))
        logger.info(f"预计抽取 {num_frames} 帧")

        # 用 ffmpeg 按间隔抽帧，输出为 jpg 图片
        output_pattern = os.path.join(tmp_dir, "frame_%04d.jpg")
        (
            ffmpeg
            .input(video_path)
            .filter("fps", fps=f"1/{interval}")
            .output(output_pattern, qscale=2)
            .run(quiet=True, overwrite_output=True)
        )

        # 读取所有抽出的帧图片
        frame_files = sorted(Path(tmp_dir).glob("frame_*.jpg"))
        frames_base64 = []

        for frame_file in frame_files:
            with open(frame_file, "rb") as f:
                frame_bytes = f.read()
                frames_base64.append(base64.b64encode(frame_bytes).decode("utf-8"))

        # 构建时间戳列表：第 i 帧对应的时间 = i * interval
        timestamps = [i * interval for i in range(len(frames_base64))]

        logger.info(f"成功抽取 {len(frames_base64)} 帧，时间戳: {timestamps}")
        return frames_base64, timestamps

    except ffmpeg.Error as e:
        stderr = e.stderr.decode("utf-8") if e.stderr else str(e)
        logger.error(f"ffmpeg 抽帧失败: {stderr}")
        raise RuntimeError(f"视频处理失败: {stderr}") from e
    finally:
        # 清理临时文件
        if tmp_dir and os.path.exists(tmp_dir):
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
