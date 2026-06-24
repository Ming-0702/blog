"""统一响应格式"""
from typing import Any
from fastapi.responses import JSONResponse


def success(data: Any = None, msg: str = "success") -> JSONResponse:
    return JSONResponse(content={"code": 0, "msg": msg, "data": data})


def fail(msg: str = "error", code: int = 1, status_code: int = 400) -> JSONResponse:
    return JSONResponse(content={"code": code, "msg": msg, "data": None}, status_code=status_code)
