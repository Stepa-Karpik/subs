from __future__ import annotations

from fastapi import Request


def success_response(data=None, request: Request | None = None, pagination: dict | None = None):
    payload = {"ok": True, "data": data}
    if pagination is not None:
        payload["pagination"] = pagination
    if request is not None:
        payload["request_id"] = getattr(request.state, "request_id", None)
    return payload


def error_response(code: str, message: str, details: dict | None = None, request: Request | None = None):
    return {
        "ok": False,
        "error": {"code": code, "message": message, "details": details or {}},
        "request_id": getattr(request.state, "request_id", None) if request is not None else None,
    }
