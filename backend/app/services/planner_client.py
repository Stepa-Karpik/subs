from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo
import httpx
from pydantic import BaseModel

from app.core.config import get_settings


class PlannerSubscriptionEventPayload(BaseModel):
    owner_subject_id: str
    calendar_title: str = "Подписки"
    external_ref: str
    title: str
    description: str = ""
    starts_at: datetime
    all_day: bool = True
    priority: int = 1
    color: str = "#111111"
    color_dark: str = "#f5f5f5"
    details_url: str | None = None


class PlannerClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        if not self.settings.planner_internal_api_key:
            return {}
        return {"x-internal-key": self.settings.planner_internal_api_key}

    def upsert_subscription_event(self, payload: PlannerSubscriptionEventPayload) -> str | None:
        if not self.settings.planner_internal_url:
            return None
        try:
            response = httpx.post(
                f"{self.settings.planner_internal_url.rstrip('/')}/subscription-events/upsert",
                json=payload.model_dump(mode="json"),
                headers=self._headers(),
                timeout=4.0,
            )
            response.raise_for_status()
            data = response.json().get("data") or response.json()
            return str(data.get("event_id")) if data.get("event_id") else None
        except httpx.HTTPError as exc:
            raise RuntimeError(str(exc)) from exc

    def delete_subscription_event(self, external_ref: str) -> None:
        if not self.settings.planner_internal_url:
            return
        try:
            response = httpx.delete(
                f"{self.settings.planner_internal_url.rstrip('/')}/subscription-events/{external_ref}",
                headers=self._headers(),
                timeout=4.0,
            )
            if response.status_code not in {200, 204, 404}:
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(str(exc)) from exc

    def delete_subscription_events_by_prefix(self, external_ref_prefix: str) -> None:
        if not self.settings.planner_internal_url:
            return
        try:
            response = httpx.delete(
                f"{self.settings.planner_internal_url.rstrip('/')}/subscription-events/by-prefix/{external_ref_prefix}",
                headers=self._headers(),
                timeout=4.0,
            )
            if response.status_code not in {200, 204, 404}:
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(str(exc)) from exc


def renewal_datetime(renewal_date, timezone_name: str = "Europe/Moscow") -> datetime:
    return datetime.combine(renewal_date, time(hour=12), ZoneInfo(timezone_name))
