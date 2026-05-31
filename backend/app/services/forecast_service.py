from __future__ import annotations

from datetime import date
from uuid import UUID
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session
from app.models.entities import BillingOccurrence, PaymentRecord, Subscription, SubscriptionGroup, SubscriptionRecommendation
from app.services.billing_calculator import add_months, month_key, next_occurrence_dates, normalize_amount
from app.services.occurrence_service import OccurrenceService


class ForecastService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_occurrences(self, owner_subject_id: str, months_ahead: int = 12) -> None:
        OccurrenceService(self.session).refresh_for_user(owner_subject_id, months_ahead=months_ahead)
        self.session.flush()

    def summary(self, owner_subject_id: str) -> dict:
        self.ensure_occurrences(owner_subject_id)
        today = date.today()
        end = add_months(today, 12)
        occurrences = self.session.scalars(select(BillingOccurrence).where(BillingOccurrence.owner_subject_id == owner_subject_id, BillingOccurrence.starts_on >= today, BillingOccurrence.starts_on < end, BillingOccurrence.status != "cancelled")).all()
        yearly = sum(o.amount_minor for o in occurrences)
        monthly = round(yearly / 12) if yearly else 0
        next_occ = min(occurrences, key=lambda o: o.starts_on, default=None)
        active_subs = self.session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == owner_subject_id, Subscription.deleted_at.is_(None), Subscription.status.in_(["active", "trial"]))) or 0
        active_groups = self.session.scalar(select(func.count(SubscriptionGroup.id)).where(SubscriptionGroup.owner_subject_id == owner_subject_id, SubscriptionGroup.deleted_at.is_(None), SubscriptionGroup.status.in_(["active", "trial"]))) or 0
        estimated = sum(o.amount_minor for o in occurrences if o.is_estimated)
        return {
            "monthly_total_minor": monthly,
            "yearly_total_minor": yearly,
            "next_payment": {"date": next_occ.starts_on.isoformat(), "amount_minor": next_occ.amount_minor, "source_type": next_occ.source_type, "source_id": str(next_occ.source_id)} if next_occ else None,
            "active_subscriptions": active_subs,
            "active_groups": active_groups,
            "estimated_minor": estimated,
            "currency": "RUB",
        }

    def monthly(self, owner_subject_id: str, months: int = 12) -> list[dict]:
        self.ensure_occurrences(owner_subject_id, months_ahead=months)
        today = date.today().replace(day=1)
        out = []
        for idx in range(months):
            start = add_months(today, idx)
            end = add_months(start, 1)
            occurrences = self.session.scalars(select(BillingOccurrence).where(BillingOccurrence.owner_subject_id == owner_subject_id, BillingOccurrence.starts_on >= start, BillingOccurrence.starts_on < end, BillingOccurrence.status != "cancelled")).all()
            payments = self.session.scalars(select(PaymentRecord).where(PaymentRecord.owner_subject_id == owner_subject_id, PaymentRecord.paid_at >= start, PaymentRecord.paid_at < end)).all()
            out.append({
                "month": month_key(start),
                "amount_minor": sum(o.amount_minor for o in occurrences),
                "paid_minor": sum(p.amount_minor for p in payments),
                "estimated_minor": sum(o.amount_minor for o in occurrences if o.is_estimated),
                "currency": "RUB",
            })
        return out

    def dashboard(self, owner_subject_id: str, month: date | None = None) -> dict:
        month = (month or date.today()).replace(day=1)
        today = date.today()
        next_month = add_months(month, 1)
        after_next = add_months(month, 2)
        year_end = add_months(month, 12)
        self.ensure_occurrences(owner_subject_id, months_ahead=14)
        current = self.session.scalars(select(BillingOccurrence).where(BillingOccurrence.owner_subject_id == owner_subject_id, BillingOccurrence.starts_on >= month, BillingOccurrence.starts_on < next_month, BillingOccurrence.status != "cancelled")).all()
        next_items = self.session.scalars(select(BillingOccurrence).where(BillingOccurrence.owner_subject_id == owner_subject_id, BillingOccurrence.starts_on >= next_month, BillingOccurrence.starts_on < after_next, BillingOccurrence.status != "cancelled")).all()
        paid = self.session.scalars(select(PaymentRecord).where(PaymentRecord.owner_subject_id == owner_subject_id, PaymentRecord.paid_at >= month, PaymentRecord.paid_at < next_month)).all()
        due = sum(o.amount_minor for o in current)
        auto_paid_sum = sum(o.amount_minor for o in current if o.starts_on < today and o.status == "predicted")
        paid_sum = sum(p.amount_minor for p in paid) + auto_paid_sum
        active_subs = self.session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == owner_subject_id, Subscription.deleted_at.is_(None), Subscription.status.in_(["active", "trial"]))) or 0
        active_groups = self.session.scalar(select(func.count(SubscriptionGroup.id)).where(SubscriptionGroup.owner_subject_id == owner_subject_id, SubscriptionGroup.deleted_at.is_(None), SubscriptionGroup.status.in_(["active", "trial"]))) or 0
        recs = self.session.scalar(select(func.count(SubscriptionRecommendation.id)).where(SubscriptionRecommendation.owner_subject_id == owner_subject_id, SubscriptionRecommendation.status == "active")) or 0
        return {
            "month": month_key(month),
            "due_this_month_minor": due,
            "paid_this_month_minor": paid_sum,
            "remaining_this_month_minor": max(due - paid_sum, 0),
            "next_month_due_minor": sum(o.amount_minor for o in next_items),
            "variable_estimated_minor": sum(o.amount_minor for o in current if o.is_estimated),
            "active_subscriptions": active_subs,
            "active_groups": active_groups,
            "recommendations_active": recs,
            "saved_this_month_minor": self._saved_between(owner_subject_id, month, next_month),
            "saved_this_year_minor": self._saved_between(owner_subject_id, month, year_end),
            "currency": "RUB",
        }

    def _saved_between(self, owner_subject_id: str, start: date, end: date) -> int:
        total = 0
        inactive_statuses = ["cancelled", "expired", "archived"]
        subs = self.session.scalars(select(Subscription).where(Subscription.owner_subject_id == owner_subject_id, Subscription.deleted_at.is_(None), Subscription.status.in_(inactive_statuses), Subscription.group_id.is_(None), Subscription.renewal_date.is_not(None))).all()
        groups = self.session.scalars(select(SubscriptionGroup).where(SubscriptionGroup.owner_subject_id == owner_subject_id, SubscriptionGroup.deleted_at.is_(None), SubscriptionGroup.status.in_(inactive_statuses), SubscriptionGroup.renewal_date.is_not(None))).all()
        for item in [*subs, *groups]:
            norm = normalize_amount(item.amount_minor, item.billing_interval, item.amount_model)
            amount = norm.interval_amount_minor or 0
            for starts_on in next_occurrence_dates(item.renewal_date, item.billing_interval, months_ahead=14, today=start):
                if start <= starts_on < end and starts_on < date.today():
                    total += amount
        return total

    def scenario(self, owner_subject_id: str, subscription_ids: list[UUID], group_ids: list[UUID]) -> dict:
        current = self.summary(owner_subject_id)["yearly_total_minor"]
        excluded = 0
        for sub in self.session.scalars(select(Subscription).where(Subscription.owner_subject_id == owner_subject_id, Subscription.id.in_(subscription_ids), Subscription.group_id.is_(None))).all():
            norm = normalize_amount(sub.amount_minor, sub.billing_interval, sub.amount_model)
            excluded += norm.yearly_minor or 0
        for group in self.session.scalars(select(SubscriptionGroup).where(SubscriptionGroup.owner_subject_id == owner_subject_id, SubscriptionGroup.id.in_(group_ids))).all():
            norm = normalize_amount(group.amount_minor, group.billing_interval, group.amount_model)
            excluded += norm.yearly_minor or 0
        return {"current_yearly_minor": current, "scenario_yearly_minor": max(current - excluded, 0), "saving_minor": min(excluded, current), "currency": "RUB"}
