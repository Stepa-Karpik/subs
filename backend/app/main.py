from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.db import Base, engine
from app.core.errors import AppError
from app.core.responses import error_response
import app.models  # noqa: F401

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.project_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id")
        return await call_next(request)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=error_response(exc.code, exc.message, exc.details, request))

    @app.get("/health")
    @app.get("/healthz")
    def health():
        return {"status": "ok", "service": "subs"}

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
