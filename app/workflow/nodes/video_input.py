"""节点: 视频输入与预处理

职责: 验证上传的视频抽帧后是否包含有效人脸
"""

import json
import logging
from openai import OpenAI
from app.config import settings
from app.workflow.state import MBTIState

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一个视频验证助手。你的任务是判断用户上传的视频画面中是否包含清晰可见的人脸。

以下是从一段视频中按时间间隔抽取的画面，每张画面标注了其在视频中出现的时间点。请综合分析这些画面并回答以下问题：
1. 视频画面中是否包含清晰可见的人脸？
2. 是否为自拍或正面/侧面的人物视频？
3. 画面质量是否足够清晰，适合进行面部特征分析？

请严格按照以下 JSON 格式回答（不要包含其他内容）：
{
    "is_valid_face": true/false,
    "description": "对视频内容的简要描述，包括人物的基本外观特征和场景"
}

如果视频不包含人脸、过于模糊、或不适合进行面部分析，请将 is_valid_face 设为 false，并在 description 中说明原因。"""


def video_input_node(state: MBTIState) -> dict:
    """视频输入预处理节点

    验证视频抽帧后是否为有效人脸画面，返回验证结果。
    """
    logger.info("[节点: video_input] 开始验证视频帧...")
    frames_base64 = state.get("frames_base64", [])
    frame_timestamps = state.get("frame_timestamps", [])
    frame_count = len(frames_base64)
    logger.info(f"[节点: video_input] 收到 {frame_count} 帧")

    if not frames_base64:
        return {
            "is_valid_face": False,
            "image_description": "",
            "error": "未收到视频帧数据",
            "is_video_input": True,
            "frame_count": 0,
        }

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    # 构建多图消息内容：将所有帧作为图片发送，并标注时间戳
    user_content = [
        {"type": "text", "text": f"这是一段视频中按时间抽取的 {frame_count} 个画面，每张标注了对应的视频时间点，请判断视频中是否包含清晰的人脸。"},
    ]
    for i, frame_b64 in enumerate(frames_base64):
        timestamp = frame_timestamps[i] if i < len(frame_timestamps) else i * 5.0
        user_content.append({"type": "text", "text": f"视频第 {timestamp:.0f} 秒的画面："})
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"},
        })

    try:
        create_params = dict(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        if not settings.ENABLE_THINKING:
            create_params["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        response = client.chat.completions.create(**create_params)

        result = json.loads(response.choices[0].message.content)

        output = {
            "is_valid_face": result.get("is_valid_face", False),
            "image_description": result.get("description", ""),
            "is_video_input": True,
            "frame_count": frame_count,
        }

        logger.info(f"[节点: video_input] 验证结果: is_valid_face={output['is_valid_face']}")
        logger.info(f"[节点: video_input] 视频描述: {output['image_description'][:100]}...")

        return output

    except Exception as e:
        return {
            "is_valid_face": False,
            "image_description": "",
            "is_video_input": True,
            "frame_count": frame_count,
            "error": f"视频预处理失败: {str(e)}",
        }
