from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.common import BaseReadModel
from app.schemas.subscription import VALID_AMOUNT_MODELS, VALID_INTERVALS, SubscriptionRead


class GroupBase(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    service_url: str | None = Field(default=None, max_length=500)
    status: str = "active"
    billing_interval: str = "monthly"
    amount_minor: int | None = Field(default=None, ge=0)
    amount_model: str = "fixed"
    estimate_strategy: str = "none"
    estimate_confidence: str = "medium"
    renewal_date: date | None = None
    notes: str | None = None

    @field_validator("billing_interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        if value not in VALID_INTERVALS:
            raise ValueError("invalid billing_interval")
        return value

    @field_validator("amount_model")
    @classmethod
    def validate_amount_model(cls, value: str) -> str:
        if value not in VALID_AMOUNT_MODELS - {"group_child"}:
            raise ValueError("invalid amount_model")
        return value

    @model_validator(mode="after")
    def validate_amount(self):
        if self.amount_model == "fixed" and self.amount_minor is None:
            raise ValueError("amount_minor is required for fixed groups")
        if self.amount_model == "free":
            self.amount_minor = 0
        return self


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    service_url: str | None = Field(default=None, max_length=500)
    status: str | None = None
    billing_interval: str | None = None
    amount_minor: int | None = Field(default=None, ge=0)
    amount_model: str | None = None
    estimate_strategy: str | None = None
    estimate_confidence: str | None = None
    renewal_date: date | None = None
    notes: str | None = None


class GroupRead(BaseReadModel):
    id: UUID
    name: str
    service_url: str | None
    status: str
    billing_interval: str
    amount_minor: int | None
    amount_model: str
    estimate_strategy: str
    estimate_confidence: str
    currency: str
    renewal_date: date | None
    calendar_event_id: str | None
    calendar_external_ref: str | None
    calendar_sync_status: str
    calendar_sync_error: str | None
    last_paid_amount_minor: int | None
    last_paid_at: datetime | None
    notes: str | None
    monthly_minor: int | None = None
    yearly_minor: int | None = None
    is_estimated: bool = False
    subscriptions: list[SubscriptionRead] = []
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class AddSubscriptionPayload(BaseModel):
    subscription_id: UUID


class RemoveSubscriptionPayload(BaseModel):
    amount_minor: int | None = Field(default=None, ge=0)
    amount_model: str = "fixed"
    billing_interval: str = "monthly"
    renewal_date: date | None = None
