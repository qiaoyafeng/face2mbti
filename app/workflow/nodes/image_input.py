"""节点1: 图片输入与预处理

职责: 验证上传图片是否为有效人脸照片
"""

import json
import logging
from openai import OpenAI
from app.config import settings
from app.workflow.state import MBTIState

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一个图片验证助手。你的任务是判断用户上传的图片是否为包含人脸的有效照片。

请分析图片并回答以下问题：
1. 图片中是否包含清晰可见的人脸？
2. 是否为自拍或正面/侧面肖像照？
3. 图片质量是否足够清晰？

请严格按照以下 JSON 格式回答（不要包含其他内容）：
{
    "is_valid_face": true/false,
    "description": "对图片的简要描述，包括人物的基本外观特征"
}

如果图片不包含人脸、过于模糊、或不适合进行面部分析，请将 is_valid_face 设为 false，并在 description 中说明原因。"""


def image_input_node(state: MBTIState) -> dict:
    """图片输入预处理节点

    验证图片是否为有效人脸照片，返回验证结果。
    """
    logger.info("[节点1: image_input] 开始验证图片...")
    image_base64 = state["image_base64"]

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    try:
        create_params = dict(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请判断这张图片是否为有效的人脸照片。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                },
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
        }
        
        logger.info(f"[节点1: image_input] 验证结果: is_valid_face={output['is_valid_face']}")
        logger.info(f"[节点1: image_input] 图片描述: {output['image_description'][:100]}...")
        
        return output

    except Exception as e:
        return {
            "is_valid_face": False,
            "image_description": "",
            "error": f"图片预处理失败: {str(e)}",
        }
