from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class UserContext(BaseModel):
    user_id: str
    username: str
    display_name: str | None = None
    email: str | None = None
    is_platform_admin: bool = False


class BaseReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    amount_minor: int
    paid_at: datetime | None = None
    note: str | None = None
    occurrence_id: UUID | None = None


class PaymentRead(BaseReadModel):
    id: UUID
    source_type: str
    source_id: UUID
    amount_minor: int
    currency: str
    paid_at: datetime
    payment_source: str
    note: str | None


class MonthlyPoint(BaseModel):
    month: str
    amount_minor: int
    paid_minor: int = 0
    estimated_minor: int = 0
    currency: str = "RUB"


class DashboardSummary(BaseModel):
    month: str
    due_this_month_minor: int
    paid_this_month_minor: int
    remaining_this_month_minor: int
    next_month_due_minor: int
    variable_estimated_minor: int
    active_subscriptions: int
    active_groups: int
    recommendations_active: int
    currency: str = "RUB"
