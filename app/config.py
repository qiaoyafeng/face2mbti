import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用配置，从 .env 文件读取"""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    ENABLE_THINKING: bool = os.getenv("ENABLE_THINKING", "false").lower() == "true"

    # 视频分析配置
    VIDEO_MAX_SIZE_MB: int = int(os.getenv("VIDEO_MAX_SIZE_MB", "50"))
    VIDEO_MAX_DURATION_SEC: int = int(os.getenv("VIDEO_MAX_DURATION_SEC", "30"))
    FRAME_INTERVAL_SEC: float = float(os.getenv("FRAME_INTERVAL_SEC", "5.0"))


settings = Settings()
