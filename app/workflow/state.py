from typing import TypedDict, Optional


class MBTIState(TypedDict, total=False):
    """LangGraph 工作流状态定义

    所有节点通过读写这个状态来传递数据。
    """

    # 输入
    image_base64: str  # 原始图片 base64 编码

    # 视频输入
    frames_base64: list  # 抽帧后的图片 base64 列表
    frame_timestamps: list  # 每帧对应的时间戳（秒）
    frame_count: int  # 帧数
    is_video_input: bool  # 是否为视频输入

    # 节点1输出: 图片预处理结果
    image_description: str  # 图片基本描述
    is_valid_face: bool  # 是否为有效人脸照片

    # 节点2输出: 面部特征分析
    face_features: str  # 面部特征详细描述

    # 节点3输出: MBTI 判断
    mbti_type: str  # MBTI 四字母结果
    dimensions: dict  # 四个维度的分析
    confidence: int  # 置信度 (0-100)

    # 节点4输出: 最终结果
    result: dict  # 最终格式化结果
    error: Optional[str]  # 错误信息
