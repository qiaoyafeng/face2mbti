"""节点2: 面部特征分析

职责: 深入分析面部特征，提取性格相关线索
"""

import logging
from openai import OpenAI
from app.config import settings
from app.workflow.state import MBTIState

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一位经验丰富的面相分析专家和心理学家。你擅长从人的面部特征、表情、气质中观察性格倾向。

请根据提供的照片，从以下维度进行详细的面部特征分析：

1. **眼神特征**: 眼神是锐利还是柔和？是聚焦还是发散？是深邃还是明亮？目光中透露出什么气质？
2. **表情特征**: 微笑类型（真诚/礼貌/腼腆/自信）、嘴角弧度、面部肌肉的松弛/紧张程度
3. **面部轮廓**: 面部线条是硬朗还是柔和？五官的比例关系？整体面部的对称性和协调感
4. **整体气质**: 给人的第一印象是内敛还是外放？是严谨还是随性？是沉稳还是活泼？
5. **穿着打扮风格**: 如果可见的话，穿着是正式还是休闲？颜色选择倾向？整体搭配风格
6. **拍照姿态**: 拍照角度选择、表情管理、与镜头的互动方式

请提供一段详细的面部特征分析文本，重点关注与性格倾向相关的特征。分析要具体、有观察依据，不要空泛。"""


def face_analysis_node(state: MBTIState) -> dict:
    """面部特征分析节点

    深入分析面部特征，提取性格相关线索。
    """
    logger.info("[节点2: face_analysis] 开始分析面部特征...")
    image_base64 = state["image_base64"]
    image_description = state.get("image_description", "")

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    user_content = f"这是一张人脸照片。基本描述：{image_description}\n\n请对这张照片进行详细的面部特征分析，重点关注与性格倾向相关的特征。"

    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                },
            ],
            temperature=0.7,
        )

        face_features = response.choices[0].message.content
        
        logger.info(f"[节点2: face_analysis] 分析完成，输出长度: {len(face_features)} 字符")
        logger.info(f"[节点2: face_analysis] 内容预览: {face_features[:200]}...")
        
        return {"face_features": face_features}

    except Exception as e:
        return {
            "face_features": "",
            "error": f"面部特征分析失败: {str(e)}",
        }
