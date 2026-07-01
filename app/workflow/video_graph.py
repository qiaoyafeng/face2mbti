"""视频分析 LangGraph 工作流定义

使用 StateGraph 将视频分析节点串联，构建视频 MBTI 分析工作流。
"""

from langgraph.graph import StateGraph, END

from app.workflow.state import MBTIState
from app.workflow.nodes.video_input import video_input_node
from app.workflow.nodes.face_analysis import face_analysis_node
from app.workflow.nodes.mbti_judge import mbti_judge_node
from app.workflow.nodes.result_format import result_format_node


def check_valid_face(state: MBTIState) -> str:
    """条件路由: 判断是否为有效人脸

    如果视频帧验证通过，继续进入面部分析节点；
    否则直接结束并返回错误。
    """
    if state.get("is_valid_face", False):
        return "face_analysis"
    else:
        return "error_end"


def error_end_node(state: MBTIState) -> dict:
    """错误结束节点: 生成错误结果"""
    error_msg = state.get("error", "上传的视频不是有效的人脸视频，请上传一段包含清晰面部的视频。")
    return {
        "result": {
            "error": True,
            "message": error_msg,
        }
    }


def build_video_graph() -> StateGraph:
    """构建并编译视频分析 LangGraph 工作流"""

    workflow = StateGraph(MBTIState)

    # 添加节点
    workflow.add_node("video_input", video_input_node)
    workflow.add_node("face_analysis", face_analysis_node)
    workflow.add_node("mbti_judge", mbti_judge_node)
    workflow.add_node("result_format", result_format_node)
    workflow.add_node("error_end", error_end_node)

    # 设置入口点
    workflow.set_entry_point("video_input")

    # 定义边（流转逻辑）
    workflow.add_conditional_edges(
        "video_input",
        check_valid_face,
        {
            "face_analysis": "face_analysis",
            "error_end": "error_end",
        },
    )
    workflow.add_edge("face_analysis", "mbti_judge")
    workflow.add_edge("mbti_judge", "result_format")
    workflow.add_edge("result_format", END)
    workflow.add_edge("error_end", END)

    return workflow.compile()


# 编译视频工作流实例
video_graph = build_video_graph()
