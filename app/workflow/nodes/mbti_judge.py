"""节点3: MBTI 类型判断

职责: 基于面部特征分析结果，判断唯一一个 MBTI 类型
"""

import json
import logging
from openai import OpenAI
from app.config import settings
from app.workflow.state import MBTIState

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是一位 MBTI 性格分析专家。你需要根据面部特征分析结果，判断这个人最可能的 MBTI 性格类型。

## 分析规则

你必须逐维度分析，每个维度做出明确判断：

1. **E（外向）vs I（内向）**: 从眼神互动性、表情开放度、拍照姿态的自如程度判断
2. **S（感觉）vs N（直觉）**: 从面部细节关注度、穿着实用性vs创意性、整体是务实还是理想化的气质判断
3. **T（思维）vs F（情感）**: 从面部线条硬朗/柔和度、表情理性/感性程度、眼神的冷静/温暖判断
4. **J（判断）vs P（感知）**: 从整体形象的规整度、表情的控制感、穿着的整齐程度判断

## 输出要求

- **只能输出一个 MBTI 类型**，不允许给出多种可能
- 每个维度给出倾向得分（50-100，表示向该方向的倾向程度）
- 给出整体置信度（0-100）
- 每个维度给出简短的判断理由

请严格按照以下 JSON 格式输出（不要包含其他内容）：
{
    "mbti_type": "XXXX",
    "confidence": 75,
    "dimensions": {
        "EI": {"result": "E或I", "score": 72, "reason": "简短判断理由"},
        "SN": {"result": "S或N", "score": 68, "reason": "简短判断理由"},
        "TF": {"result": "T或F", "score": 80, "reason": "简短判断理由"},
        "JP": {"result": "J或P", "score": 65, "reason": "简短判断理由"}
    }
}"""


def mbti_judge_node(state: MBTIState) -> dict:
    """MBTI 类型判断节点

    基于面部特征分析，判断唯一一个 MBTI 类型。
    """
    logger.info("[节点3: mbti_judge] 开始判断 MBTI 类型...")
    face_features = state.get("face_features", "")

    if not face_features:
        return {
            "mbti_type": "",
            "dimensions": {},
            "confidence": 0,
            "error": "缺少面部特征分析数据",
        }

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )

    user_content = f"""以下是对一张人脸照片的详细面部特征分析：

{face_features}

请根据以上面部特征分析，判断这个人最可能的 MBTI 性格类型。记住：只能给出一个确定的结果。"""

    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        output = {
            "mbti_type": result.get("mbti_type", ""),
            "dimensions": result.get("dimensions", {}),
            "confidence": result.get("confidence", 0),
        }
        
        logger.info(f"[节点3: mbti_judge] MBTI 结果: {output['mbti_type']} (置信度: {output['confidence']}%)")
        logger.info(f"[节点3: mbti_judge] 维度分析: {output['dimensions']}")
        
        return output

    except Exception as e:
        return {
            "mbti_type": "",
            "dimensions": {},
            "confidence": 0,
            "error": f"MBTI 判断失败: {str(e)}",
        }
