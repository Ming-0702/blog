"""应用配置"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用基础配置
    APP_NAME: str = "MyBlog"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/blog"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/blog"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # 博客作者（唯一可发布文章的用户）
    AUTHOR_USERNAME: str = "lg鹿铭"

    # AI 摘要（OpenAI 兼容 API）
    AI_API_KEY: str = ""
    AI_API_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-3.5-turbo"

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:5173/auth/github/callback"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
