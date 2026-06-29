"""节点4: 结果格式化输出

职责: 将分析结果整合为最终展示格式
"""

import logging
from app.workflow.state import MBTIState

logger = logging.getLogger(__name__)


# MBTI 16种类型的中文昵称和简短描述
MBTI_INFO = {
    "ISTJ": {"nickname": "检查员", "description": "安静、严肃，通过全面性和可靠性来达成目标。务实、有条理、注重事实、有逻辑、现实且可靠。"},
    "ISFJ": {"nickname": "守护者", "description": "安静、友善、有责任感且尽职尽责。坚定地完成自己的义务，为他人提供温暖与照顾。"},
    "INFJ": {"nickname": "提倡者", "description": "寻求思想、关系和物质之间的意义和联系。富有洞察力，致力于坚定的价值观。"},
    "INTJ": {"nickname": "建筑师", "description": "对于实现自己的想法和达成目标有着强烈的驱动力。能很快洞察到外部事物中的规律并形成长期的远景计划。"},
    "ISTP": {"nickname": "鉴赏家", "description": "容忍且灵活，是安静的观察者，直到问题出现，然后迅速行动找到可行的解决方案。"},
    "ISFP": {"nickname": "探险家", "description": "安静、友善、敏感且善良。享受当下，喜欢按照自己的节奏在自己的空间做事。"},
    "INFP": {"nickname": "调停者", "description": "理想主义，对自己认为重要的事业忠诚。寻求理解他人并帮助他们发挥潜能。"},
    "INTP": {"nickname": "逻辑学家", "description": "对任何引起兴趣的事物寻求合乎逻辑的解释。喜欢理论和抽象的事物，热爱思考。"},
    "ESTP": {"nickname": "企业家", "description": "灵活且容忍，采取务实的方法来取得即时的结果。专注于此时此刻，享受每一刻的活跃。"},
    "ESFP": {"nickname": "表演者", "description": "外向、友善且接纳他人。热爱生活、人物和物质享受。喜欢与他人合作使事情发生。"},
    "ENFP": {"nickname": "竞选者", "description": "热情且富有想象力。觉得生活充满可能性。能很快将事件和信息联系起来，自信地根据看到的模式行动。"},
    "ENTP": {"nickname": "辩论家", "description": "机智、聪明，能激励他人。警觉且直言不讳。足智多谋地解决新的、有挑战性的问题。"},
    "ESTJ": {"nickname": "总经理", "description": "务实，注重现实，实事求是。果断，一旦做出决定就迅速行动。善于组织项目和人员来完成事情。"},
    "ESFJ": {"nickname": "执政官", "description": "热心且有合作精神，希望周围的环境温馨和谐。喜欢与他人合作，精确且及时地完成任务。"},
    "ENFJ": {"nickname": "主人公", "description": "热情且有责任感，富有同理心。高度关注他人的情感和需求。善于发现每个人的潜能并希望帮助他人实现。"},
    "ENTJ": {"nickname": "指挥官", "description": "坦率，果断，乐于承担领导者的角色。善于发现不合理和低效的程序，并开发和实施全面的系统来解决问题。"},
}


def result_format_node(state: MBTIState) -> dict:
    """结果格式化节点

    将分析结果整合为最终展示格式。
    """
    logger.info("[节点4: result_format] 开始格式化结果...")
    mbti_type = state.get("mbti_type", "")
    dimensions = state.get("dimensions", {})
    confidence = state.get("confidence", 0)
    face_features = state.get("face_features", "")

    # 获取 MBTI 类型信息
    type_info = MBTI_INFO.get(mbti_type.upper(), {
        "nickname": "未知类型",
        "description": "无法识别的 MBTI 类型"
    })

    # 组装最终结果
    result = {
        "mbti_type": mbti_type.upper(),
        "nickname": type_info["nickname"],
        "description": type_info["description"],
        "confidence": confidence,
        "dimensions": dimensions,
        "face_analysis": face_features,
    }

    logger.info(f"[节点4: result_format] 格式化完成: {result['mbti_type']} - {result['nickname']}")
    
    return {"result": result}
