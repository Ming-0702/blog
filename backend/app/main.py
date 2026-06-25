"""FastAPI 应用主入口"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, users, posts, comments, likes, websocket, automation


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 初始化自动化调度器
    from app.services.scheduler import init_scheduler, scheduler
    init_scheduler()
    yield
    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(posts.router, prefix=API_PREFIX)
app.include_router(comments.router, prefix=API_PREFIX)
app.include_router(likes.router, prefix=API_PREFIX)
app.include_router(automation.router, prefix=API_PREFIX)
app.include_router(websocket.router)

# 静态文件（头像等）
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.get("/")
async def root():
    return {"app": settings.APP_NAME, "version": "0.1.0", "status": "running"}
