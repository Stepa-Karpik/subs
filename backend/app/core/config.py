from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_name: str = "Nerior Subs"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./subs.db"
    identity_internal_url: str = "http://127.0.0.1:8300/api/v1"
    planner_internal_url: str = "http://127.0.0.1:8000/api/v1"
    documents_internal_url: str = "http://127.0.0.1:8200/api/v1"
    ai_runtime_internal_url: str = "http://127.0.0.1:8330/api/v1"
    auth_login_url: str = "https://auth.nerior.ru/login"
    allow_dev_auth: bool = True
    subs_internal_api_key: str = ""
    planner_internal_api_key: str = ""
    account_identifier_encryption_key: str = "change-this-secret"
    account_identifier_hash_pepper: str = "change-this-pepper"
    cors_origins: list[str] = [
        "https://subs.nerior.ru",
        "https://planner.nerior.ru",
        "https://documents.nerior.ru",
        "https://crm.nerior.ru",
        "https://admin.nerior.ru",
        "http://localhost:3000",
        "http://localhost:3400",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
