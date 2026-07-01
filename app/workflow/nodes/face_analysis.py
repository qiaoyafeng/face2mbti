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


SYSTEM_PROMPT_VIDEO = """你是一位经验丰富的面相分析专家和心理学家。你擅长从人的面部特征、表情、气质以及肢体语言中观察性格倾向。

以下是从一段视频中按时间间隔抽取的画面，每张画面标注了其在视频中出现的时间点（如“视频第 5 秒”）。请根据这些画面，从以下维度进行详细的面部特征分析：

1. **眼神特征**: 眼神是锐利还是柔和？是聚焦还是发散？是深邃还是明亮？目光中透露出什么气质？在不同时间点眼神有无变化？
2. **表情特征**: 微笑类型（真诚/礼貌/腼莦/自信）、嘴角弧度、面部肌肉的松弛/紧张程度，在不同时间点表情有无变化？
3. **面部轮廓**: 面部线条是硬朗还是柔和？五官的比例关系？整体面部的对称性和协调感
4. **整体气质**: 给人的第一印象是内敛还是外放？是严谨还是随性？是沉稳还是活泼？
5. **穿着打扮风格**: 如果可见的话，穿着是正式还是休闲？颜色选择倾向？整体搭配风格
6. **肢体语言与动作**: 画面中可以观察到的手势、身体姿态、头部动作等，这些动态特征往往能反映性格倾向
7. **场景与互动**: 视频场景是室内还是室外？与镜头的互动方式如何？是自然随意还是有意识展示？

**重要**: 在分析中引用具体画面时，请使用时间点来引用（例如“视频第 5 秒时表情变为...”），而不是用帧序号。

请提供一段详细的面部特征分析文本，重点关注与性格倾向相关的特征。分析要具体、有观察依据，不要空泛。"""


def face_analysis_node(state: MBTIState) -> dict:
    """面部特征分析节点

    深入分析面部特征，提取性格相关线索。
    """
    logger.info("[节点2: face_analysis] 开始分析面部特征...")
    is_video = state.get("is_video_input", False)

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    try:
        if is_video:
            # 视频模式：多帧输入，标注时间戳
            frames_base64 = state.get("frames_base64", [])
            frame_timestamps = state.get("frame_timestamps", [])
            image_description = state.get("image_description", "")
            frame_count = len(frames_base64)

            user_content = [
                {"type": "text", "text": f"这是一段视频中按时间抽取的 {frame_count} 个画面，每张标注了对应的视频时间点。基本描述：{image_description}\n\n请综合分析这些视频画面，进行详细的面部特征分析，重点关注与性格倾向相关的特征，以及视频中动态表现出的性格线索。引用具体画面时请使用时间点（如“视频第 5 秒时...”）。"},
            ]
            for i, frame_b64 in enumerate(frames_base64):
                timestamp = frame_timestamps[i] if i < len(frame_timestamps) else i * 5.0
                user_content.append({"type": "text", "text": f"视频第 {timestamp:.0f} 秒的画面："})
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"},
                })

            create_params = dict(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_VIDEO},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
            )
        else:
            # 图片模式：单图输入（原有逻辑）
            image_base64 = state["image_base64"]
            image_description = state.get("image_description", "")

            user_content = f"这是一张人脸照片。基本描述：{image_description}\n\n请对这张照片进行详细的面部特征分析，重点关注与性格倾向相关的特征。"

            create_params = dict(
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

        if not settings.ENABLE_THINKING:
            create_params["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        response = client.chat.completions.create(**create_params)

        face_features = response.choices[0].message.content
        
        logger.info(f"[节点2: face_analysis] 分析完成，输出长度: {len(face_features)} 字符")
        logger.info(f"[节点2: face_analysis] 内容预览: {face_features[:200]}...")
        
        return {"face_features": face_features}

    except Exception as e:
        return {
            "face_features": "",
            "error": f"面部特征分析失败: {str(e)}",
        }
