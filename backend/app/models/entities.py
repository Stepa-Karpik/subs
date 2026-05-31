from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.db import Base
from app.core.types import GUID


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


JsonType = JSON().with_variant(JSONB, "postgresql")


class SubscriptionGroup(Base):
    __tablename__ = "subscription_groups"
    __table_args__ = (
        Index("ix_groups_owner_status_renewal", "owner_subject_id", "status", "renewal_date"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_subject_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), default="personal", index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(128), index=True)
    project_id: Mapped[str | None] = mapped_column(String(128), index=True)
    company_id: Mapped[str | None] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    service_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    billing_interval: Mapped[str] = mapped_column(String(32), default="monthly", index=True)
    amount_minor: Mapped[int | None] = mapped_column(Integer)
    amount_model: Mapped[str] = mapped_column(String(32), default="fixed", index=True)
    estimate_strategy: Mapped[str] = mapped_column(String(48), default="none")
    estimate_confidence: Mapped[str] = mapped_column(String(32), default="medium")
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    renewal_date: Mapped[date | None] = mapped_column(Date, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    calendar_event_id: Mapped[str | None] = mapped_column(String(128), index=True)
    calendar_external_ref: Mapped[str | None] = mapped_column(String(220), unique=True)
    calendar_sync_status: Mapped[str] = mapped_column(String(32), default="not_synced", index=True)
    calendar_sync_error: Mapped[str | None] = mapped_column(Text)
    last_paid_amount_minor: Mapped[int | None] = mapped_column(Integer)
    last_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_subject_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="group")


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_owner_status_renewal", "owner_subject_id", "status", "renewal_date"),
        Index("ix_subscriptions_owner_category", "owner_subject_id", "category_key"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_subject_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), default="personal", index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(128), index=True)
    project_id: Mapped[str | None] = mapped_column(String(128), index=True)
    company_id: Mapped[str | None] = mapped_column(String(128), index=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("subscription_groups.id"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    service_url: Mapped[str | None] = mapped_column(String(500))
    account_identifier_encrypted: Mapped[str | None] = mapped_column(Text)
    account_identifier_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    category_key: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    billing_interval: Mapped[str] = mapped_column(String(32), default="monthly", index=True)
    amount_minor: Mapped[int | None] = mapped_column(Integer)
    amount_model: Mapped[str] = mapped_column(String(32), default="fixed", index=True)
    estimate_strategy: Mapped[str] = mapped_column(String(48), default="none")
    estimate_confidence: Mapped[str] = mapped_column(String(32), default="medium")
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    renewal_date: Mapped[date | None] = mapped_column(Date, index=True)
    trial_end_date: Mapped[date | None] = mapped_column(Date, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Moscow")
    calendar_event_id: Mapped[str | None] = mapped_column(String(128), index=True)
    calendar_external_ref: Mapped[str | None] = mapped_column(String(220), unique=True)
    calendar_sync_status: Mapped[str] = mapped_column(String(32), default="not_synced", index=True)
    calendar_sync_error: Mapped[str | None] = mapped_column(Text)
    last_paid_amount_minor: Mapped[int | None] = mapped_column(Integer)
    last_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_subject_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    group: Mapped[SubscriptionGroup | None] = relationship(back_populates="subscriptions")


class SubscriptionPriceHistory(Base):
    __tablename__ = "subscription_price_history"

    id: Mapped[uuid.UUID] = uuid_pk()
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("subscriptions.id"), index=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("subscription_groups.id"), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    billing_interval: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by_subject_id: Mapped[str | None] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(32), default="user")
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class BillingOccurrence(Base):
    __tablename__ = "billing_occurrences"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", "starts_on", name="uq_billing_occurrence"),
        Index("ix_occurrences_owner_starts", "owner_subject_id", "starts_on"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_subject_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    starts_on: Mapped[date] = mapped_column(Date, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    is_estimated: Mapped[bool] = mapped_column(default=False)
    estimate_confidence: Mapped[str] = mapped_column(String(32), default="exact")
    status: Mapped[str] = mapped_column(String(32), default="predicted", index=True)
    calendar_event_id: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class PaymentRecord(Base):
    __tablename__ = "payment_records"
    __table_args__ = (Index("ix_payments_owner_paid", "owner_subject_id", "paid_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_subject_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    occurrence_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("billing_occurrences.id"), index=True)
    source_type: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    payment_source: Mapped[str] = mapped_column(String(32), default="user_manual")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class RegionalCostBaseline(Base):
    __tablename__ = "regional_cost_baselines"
    __table_args__ = (UniqueConstraint("country_code", "city", "category_key", "billing_interval", name="uq_regional_baseline"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    country_code: Mapped[str] = mapped_column(String(2), index=True)
    city: Mapped[str | None] = mapped_column(String(120), index=True)
    category_key: Mapped[str] = mapped_column(String(64), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    billing_interval: Mapped[str] = mapped_column(String(32), default="monthly")
    source_name: Mapped[str] = mapped_column(String(160), default="manual")
    source_updated_at: Mapped[date | None] = mapped_column(Date)
    confidence: Mapped[str] = mapped_column(String(32), default="low")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class SubscriptionRecommendation(Base):
    __tablename__ = "subscription_recommendations"
    __table_args__ = (Index("ix_recommendations_owner_status", "owner_subject_id", "status"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_subject_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), index=True)
    target_id: Mapped[uuid.UUID] = mapped_column(GUID(), index=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), default="info", index=True)
    confidence: Mapped[float] = mapped_column(Numeric(5, 2), default=0.5)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_saving_minor: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class SubscriptionDocumentLink(Base):
    __tablename__ = "subscription_document_links"

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_subject_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("subscriptions.id"), index=True)
    group_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("subscription_groups.id"), index=True)
    document_id: Mapped[str] = mapped_column(String(128), index=True)
    document_title_snapshot: Mapped[str | None] = mapped_column(String(260))
    relation_type: Mapped[str] = mapped_column(String(48), default="other")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (Index("ix_audit_owner_created", "owner_subject_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_subject_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    actor_subject_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(120), index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[str] = mapped_column(String(128), index=True)
    payload_json: Mapped[dict] = mapped_column(JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
