from __future__ import annotations

from pydantic import BaseModel


class IntegrationStatus(BaseModel):
    planner_calendar_title: str = "Подписки"
    failed_sync_count: int = 0
    pending_sync_count: int = 0
    synced_count: int = 0
    last_error: str | None = None
