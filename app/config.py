import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用配置，从 .env 文件读取"""

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4o")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))


settings = Settings()
