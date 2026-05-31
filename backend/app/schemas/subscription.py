from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from app.schemas.common import BaseReadModel

VALID_INTERVALS = {"weekly", "monthly", "semi_annual", "annual"}
VALID_AMOUNT_MODELS = {"fixed", "variable", "custom", "free", "group_child", "unknown"}


class SubscriptionBase(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    service_url: str | None = Field(default=None, max_length=500)
    account_identifier: str | None = Field(default=None, max_length=255)
    category_key: str | None = Field(default=None, max_length=64)
    status: str = "active"
    billing_interval: str = "monthly"
    amount_minor: int | None = Field(default=None, ge=0)
    amount_model: str = "fixed"
    estimate_strategy: str = "none"
    estimate_confidence: str = "medium"
    renewal_date: date | None = None
    trial_end_date: date | None = None
    notes: str | None = None
    group_id: UUID | None = None

    @field_validator("billing_interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        if value not in VALID_INTERVALS:
            raise ValueError("invalid billing_interval")
        return value

    @field_validator("amount_model")
    @classmethod
    def validate_amount_model(cls, value: str) -> str:
        if value not in VALID_AMOUNT_MODELS:
            raise ValueError("invalid amount_model")
        return value

    @model_validator(mode="after")
    def validate_amount(self):
        if self.group_id is not None:
            self.amount_model = "group_child"
            self.amount_minor = None
        if self.amount_model == "fixed" and self.amount_minor is None:
            raise ValueError("amount_minor is required for fixed subscriptions")
        if self.amount_model == "free":
            self.amount_minor = 0
        if self.amount_model == "group_child" and self.amount_minor is not None:
            raise ValueError("group child subscriptions cannot have own price")
        return self


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    service_url: str | None = Field(default=None, max_length=500)
    account_identifier: str | None = Field(default=None, max_length=255)
    category_key: str | None = Field(default=None, max_length=64)
    status: str | None = None
    billing_interval: str | None = None
    amount_minor: int | None = Field(default=None, ge=0)
    amount_model: str | None = None
    estimate_strategy: str | None = None
    estimate_confidence: str | None = None
    renewal_date: date | None = None
    trial_end_date: date | None = None
    notes: str | None = None
    group_id: UUID | None = None


class SubscriptionRead(BaseReadModel):
    id: UUID
    group_id: UUID | None
    name: str
    service_url: str | None
    account_identifier_masked: str | None = None
    category_key: str | None
    status: str
    billing_interval: str
    amount_minor: int | None
    amount_model: str
    estimate_strategy: str
    estimate_confidence: str
    currency: str
    renewal_date: date | None
    trial_end_date: date | None
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
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class MoveToGroupPayload(BaseModel):
    group_id: UUID
