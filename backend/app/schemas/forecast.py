from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel
from app.schemas.common import MonthlyPoint


class ForecastSummary(BaseModel):
    monthly_total_minor: int
    yearly_total_minor: int
    next_payment: dict | None
    active_subscriptions: int
    active_groups: int
    estimated_minor: int
    currency: str = "RUB"


class ForecastMonthly(BaseModel):
    months: list[MonthlyPoint]


class ScenarioRequest(BaseModel):
    subscription_ids: list[UUID] = []
    group_ids: list[UUID] = []


class ScenarioResponse(BaseModel):
    current_yearly_minor: int
    scenario_yearly_minor: int
    saving_minor: int
    currency: str = "RUB"
