"""AI 调用工具 —— 共享的 OpenAI 兼容 API 调用"""
import httpx
from app.core.config import settings


async def ai_chat(
    system_prompt: str,
    user_content: str,
    max_tokens: int = 500,
    temperature: float = 0.7,
    timeout: int = 30,
) -> str | None:
    """调用 OpenAI 兼容 API，返回 AI 生成的文本。
    当 AI_API_KEY 未配置时返回 None。
    """
    if not settings.AI_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{settings.AI_API_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                json={
                    "model": settings.AI_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            result = resp.json()
            return result["choices"][0]["message"]["content"].strip()
    except Exception:
        return None
