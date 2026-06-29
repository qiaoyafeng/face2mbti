# Face2MBTI - 看脸测 MBTI 性格分析智能体

基于 **LangGraph 节点式工作流** 的 AI 性格分析应用，上传一张自拍照片，AI 帮你分析最可能的 MBTI 性格类型。

![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)
![LangGraph](https://img.shields.io/badge/framework-LangGraph-purple)
![FastAPI](https://img.shields.io/badge/web-FastAPI-green)

---

## 特性

- **节点式工作流** — 使用 LangGraph StateGraph 编排四个分析节点，逻辑清晰、易扩展
- **多模态 AI 分析** — 调用 OpenAI 协议兼容的多模态大模型，从面部特征推断性格
- **单结果输出** — 严格只返回一个 MBTI 类型，不做多类型推荐
- **四维度分析** — 展示 E/I、S/N、T/F、J/P 每个维度的得分与判断理由
- **灵活配置** — 通过 `.env` 文件切换任意 OpenAI 兼容 API（豆包、通义、Gemini 等）
- **响应式界面** — 支持拖拽上传，移动端友好

---

## 工作流架构

```
┌──────────────┐     有效人脸     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  图片输入    │ ──────────────→ │  面部特征    │ ──→ │  MBTI判断    │ ──→ │  结果格式化  │ → 返回
│  预处理节点  │                 │  分析节点    │     │  节点        │     │  节点        │
└──────────────┘                 └──────────────┘     └──────────────┘     └──────────────┘
       │
       │ 非有效人脸
       ↓
   返回错误提示
```

**节点说明：**

| 节点 | 文件 | 职责 |
|------|------|------|
| 图片输入 | `app/workflow/nodes/image_input.py` | 验证照片是否为有效人脸 |
| 面部分析 | `app/workflow/nodes/face_analysis.py` | 从多维度分析面部特征，提取性格线索 |
| MBTI 判断 | `app/workflow/nodes/mbti_judge.py` | 逐维度推理，确定唯一 MBTI 类型 |
| 结果格式化 | `app/workflow/nodes/result_format.py` | 补充类型昵称、描述，组装最终结果 |

---

## 快速开始

### 环境要求

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) 包管理器（推荐）
- 任意 OpenAI 协议兼容的多模态 API

### 安装与运行

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd face2mbti

# 2. 安装依赖（uv 会自动创建虚拟环境）
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API 配置

# 4. 启动服务
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. 浏览器访问
open http://localhost:8000
```

### 环境变量配置

复制 `.env.example` 为 `.env` 并填写：

```env
# OpenAI 兼容 API 密钥
OPENAI_API_KEY=your-api-key

# API 基础地址（默认为 OpenAI，可换成其他兼容接口）
OPENAI_BASE_URL=https://api.openai.com/v1

# 使用的多模态模型名称
MODEL_NAME=gpt-4o
```

> 支持任何遵循 OpenAI 协议的多模态接口，如豆包视觉大模型、通义千问 VL、Gemini 等，只需修改 `OPENAI_BASE_URL` 和 `MODEL_NAME`。

---

## 项目结构

```
face2mbti/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理（读取 .env）
│   ├── workflow/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph 工作流编排
│   │   ├── state.py             # 工作流状态定义（TypedDict）
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── image_input.py   # 节点1：图片预处理与验证
│   │       ├── face_analysis.py # 节点2：面部特征分析
│   │       ├── mbti_judge.py    # 节点3：MBTI 类型判断
│   │       └── result_format.py # 节点4：结果格式化
│   └── static/
│       ├── index.html           # 前端页面
│       ├── style.css            # 样式
│       └── script.js            # 交互逻辑
├── .env.example                 # 环境变量示例
├── pyproject.toml               # 项目元数据与依赖
└── uv.lock                      # uv 锁定文件
```

---

## API 接口

### `POST /api/analyze`

上传自拍照片进行 MBTI 分析。

**请求：**
- `Content-Type: multipart/form-data`
- Body: `file` (图片文件，支持 JPG/PNG/WebP，最大 10MB)

**响应示例：**

```json
{
  "mbti_type": "INFP",
  "nickname": "调停者",
  "confidence": 78,
  "description": "理想主义，对自己认为重要的事业忠诚...",
  "dimensions": {
    "EI": {"result": "I", "score": 72, "reason": "眼神柔和内敛..."},
    "SN": {"result": "N", "score": 80, "reason": "面部表情富有想象力..."},
    "TF": {"result": "F", "score": 65, "reason": "嘴角微扬，面部线条柔和..."},
    "JP": {"result": "P", "score": 70, "reason": "整体气质自由随性..."}
  },
  "face_analysis": "详细面部特征分析文本..."
}
```

---

## 常见问题

**Q: 支持哪些模型？**
A: 任何兼容 OpenAI `chat.completions` 接口且支持 `image_url` 的多模态模型均可。

**Q: 分析结果准确吗？**
A: 仅供娱乐参考，面部特征与性格类型无科学因果关系。

**Q: 图片上传后报错"非有效人脸"？**
A: 确保照片中包含清晰、正面或侧面的人脸，避免使用风景照、动物照或过度模糊的照片。

---

## 技术栈

- **后端**: FastAPI + LangGraph + LangChain
- **AI**: OpenAI 协议多模态大模型
- **前端**: 原生 HTML/CSS/JavaScript
- **环境管理**: uv

---

## License

MIT
