"""Face2MBTI - FastAPI Web 服务入口"""

import base64
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.workflow.graph import graph

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = FastAPI(title="Face2MBTI", description="看脸测 MBTI 性格分析")

# 静态文件目录
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def index():
    """返回前端页面"""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    """接收上传的图片，调用 LangGraph 工作流进行 MBTI 分析

    Args:
        file: 上传的图片文件（支持 jpg/png/webp）

    Returns:
        MBTI 分析结果 JSON
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件")

    # 限制文件大小 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片文件过大，请上传小于 10MB 的图片")

    # 将图片转为 base64
    image_base64 = base64.b64encode(contents).decode("utf-8")

    # 调用 LangGraph 工作流
    try:
        result = graph.invoke({"image_base64": image_base64})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析过程出错: {str(e)}")

    # 返回结果
    final_result = result.get("result")
    if not final_result:
        raise HTTPException(status_code=500, detail="分析未返回结果")

    return final_result


@app.post("/api/analyze/debug")
async def analyze_debug(file: UploadFile = File(...)):
    """调试接口: 返回每个节点的输出内容

    Args:
        file: 上传的图片文件（支持 jpg/png/webp）

    Returns:
        包含所有节点输出的 JSON
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传有效的图片文件")

    # 限制文件大小 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片文件过大，请上传小于 10MB 的图片")

    # 将图片转为 base64
    image_base64 = base64.b64encode(contents).decode("utf-8")

    # 逐节点收集输出
    node_outputs = {}
    try:
        for event in graph.stream({"image_base64": image_base64}):
            for node_name, node_output in event.items():
                node_outputs[node_name] = node_output
    except Exception as e:
        node_outputs["error"] = str(e)

    return node_outputs


# 挂载静态文件（CSS、JS 等）
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
