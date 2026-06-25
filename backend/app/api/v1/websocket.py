"""WebSocket 实时通知"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

from app.core.security import decode_access_token
from app.core.database import async_session
from app.models import User
from sqlalchemy import select

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# {user_id: {WebSocket, ...}}
active_connections: Dict[int, Set[WebSocket]] = {}


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket, token: str):
    """WebSocket 连接端点"""
    payload = decode_access_token(token)
    if not payload or not payload.get("user_id"):
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload["user_id"]
    await websocket.accept()

    # 注册连接
    if user_id not in active_connections:
        active_connections[user_id] = set()
    active_connections[user_id].add(websocket)

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        active_connections[user_id].discard(websocket)
        if not active_connections[user_id]:
            del active_connections[user_id]


async def notify_user(user_id: int, notification_type: str, data: dict):
    """向指定用户发送通知"""
    if user_id not in active_connections:
        return
    message = json.dumps({"type": notification_type, "data": data})
    dead: set = set()
    for ws in active_connections[user_id]:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    active_connections[user_id] -= dead
