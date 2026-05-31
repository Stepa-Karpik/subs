from __future__ import annotations

from datetime import date
from sqlalchemy import and_, select
from sqlalchemy.orm import Session
from app.models.entities import BillingOccurrence, Subscription, SubscriptionGroup
from app.services.billing_calculator import next_occurrence_dates

ACTIVE_STATUSES = {"active", "trial"}
PAYMENT_MODELS = {"fixed", "variable", "custom", "free"}


class OccurrenceService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def refresh_for_user(self, owner_subject_id: str, months_ahead: int = 12, today: date | None = None) -> None:
        today = today or date.today()
        subscriptions = self.session.scalars(
            select(Subscription).where(
                Subscription.owner_subject_id == owner_subject_id,
                Subscription.deleted_at.is_(None),
                Subscription.status.in_(ACTIVE_STATUSES),
                Subscription.group_id.is_(None),
                Subscription.renewal_date.is_not(None),
                Subscription.amount_model.in_(PAYMENT_MODELS),
            )
        ).all()
        groups = self.session.scalars(
            select(SubscriptionGroup).where(
                SubscriptionGroup.owner_subject_id == owner_subject_id,
                SubscriptionGroup.deleted_at.is_(None),
                SubscriptionGroup.status.in_(ACTIVE_STATUSES),
                SubscriptionGroup.renewal_date.is_not(None),
                SubscriptionGroup.amount_model.in_(PAYMENT_MODELS),
            )
        ).all()
        for item in subscriptions:
            self._upsert_occurrences("subscription", item.id, owner_subject_id, item.renewal_date, item.billing_interval, item.amount_minor or 0, item.currency, item.amount_model, item.estimate_confidence, months_ahead, today)
        for item in groups:
            self._upsert_occurrences("group", item.id, owner_subject_id, item.renewal_date, item.billing_interval, item.amount_minor or 0, item.currency, item.amount_model, item.estimate_confidence, months_ahead, today)

    def _upsert_occurrences(self, source_type, source_id, owner_subject_id, renewal_date, interval, amount_minor, currency, amount_model, confidence, months_ahead, today):
        for starts_on in next_occurrence_dates(renewal_date, interval, months_ahead=months_ahead, today=today):
            existing = self.session.scalar(select(BillingOccurrence).where(and_(BillingOccurrence.source_type == source_type, BillingOccurrence.source_id == source_id, BillingOccurrence.starts_on == starts_on)))
            is_estimated = amount_model in {"variable", "custom"}
            if existing:
                if existing.status != "paid":
                    existing.amount_minor = amount_minor
                    existing.currency = currency
                    existing.is_estimated = is_estimated
                    existing.estimate_confidence = "exact" if not is_estimated else confidence
                continue
            self.session.add(BillingOccurrence(
                owner_subject_id=owner_subject_id,
                source_type=source_type,
                source_id=source_id,
                starts_on=starts_on,
                amount_minor=amount_minor,
                currency=currency,
                is_estimated=is_estimated,
                estimate_confidence="exact" if not is_estimated else confidence,
                status="predicted",
            ))
