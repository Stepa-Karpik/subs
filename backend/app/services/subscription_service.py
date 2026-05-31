from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import NotFoundError, ValidationAppError
from app.core.security import encrypt_text, hash_identifier
from app.models.entities import BillingOccurrence, PaymentRecord, Subscription, SubscriptionGroup, SubscriptionPriceHistory
from app.schemas.common import PaymentCreate
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from app.services.audit import write_audit
from app.services.calendar_sync_service import CalendarSyncService
from app.services.variable_estimate_service import VariableEstimateService


VARIABLE_DEFAULT_CATEGORIES = {"utilities", "electricity", "water", "heating", "gas", "mobile_usage"}


class SubscriptionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    def _apply_account(self, item: Subscription, account_identifier: str | None) -> None:
        item.account_identifier_encrypted = encrypt_text(account_identifier, self.settings.account_identifier_encryption_key)
        item.account_identifier_hash = hash_identifier(account_identifier, self.settings.account_identifier_hash_pepper)

    def _validate_group(self, owner_subject_id: str, group_id: UUID | None) -> SubscriptionGroup | None:
        if group_id is None:
            return None
        group = self.session.get(SubscriptionGroup, group_id)
        if group is None or group.owner_subject_id != owner_subject_id or group.deleted_at is not None:
            raise NotFoundError("Group not found")
        return group

    def create(self, owner_subject_id: str, actor_subject_id: str, payload: SubscriptionCreate) -> Subscription:
        group = self._validate_group(owner_subject_id, payload.group_id)
        amount_model = payload.amount_model
        amount_minor = payload.amount_minor
        renewal_date = payload.renewal_date
        billing_interval = payload.billing_interval
        if group:
            amount_model = "group_child"
            amount_minor = None
            renewal_date = group.renewal_date
            billing_interval = group.billing_interval
        if payload.category_key in VARIABLE_DEFAULT_CATEGORIES and amount_model == "fixed":
            amount_model = "variable"
        item = Subscription(
            owner_subject_id=owner_subject_id,
            created_by_subject_id=actor_subject_id,
            group_id=payload.group_id,
            name=payload.name.strip(),
            service_url=payload.service_url,
            category_key=payload.category_key,
            status=payload.status,
            billing_interval=billing_interval,
            amount_minor=amount_minor,
            amount_model=amount_model,
            estimate_strategy=payload.estimate_strategy,
            estimate_confidence=payload.estimate_confidence,
            renewal_date=renewal_date,
            trial_end_date=payload.trial_end_date,
            notes=payload.notes,
        )
        self._apply_account(item, payload.account_identifier)
        if item.amount_model == "variable" and item.amount_minor is None:
            estimate = VariableEstimateService(self.session).estimate(owner_subject_id=owner_subject_id, source_type="subscription", source_id=item.id, category_key=item.category_key)
            item.amount_minor = estimate.amount_minor
            item.estimate_strategy = estimate.strategy
            item.estimate_confidence = estimate.confidence
        self.session.add(item)
        self.session.flush()
        self._write_price_history(item, actor_subject_id)
        self._sync(item)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="subscription_created", target_type="subscription", target_id=str(item.id), payload={"name": item.name})
        self.session.commit()
        self.session.refresh(item)
        return item

    def list(self, owner_subject_id: str, *, q: str | None = None, status: str | None = None, interval: str | None = None, category: str | None = None, group_id: UUID | None = None, limit: int = 100, offset: int = 0):
        stmt = select(Subscription).where(Subscription.owner_subject_id == owner_subject_id, Subscription.deleted_at.is_(None))
        if q:
            value = q.strip()
            pattern = f"%{value}%"
            account_hash = hash_identifier(value, self.settings.account_identifier_hash_pepper)
            stmt = stmt.where(or_(Subscription.name.ilike(pattern), Subscription.service_url.ilike(pattern), Subscription.category_key.ilike(pattern), Subscription.account_identifier_hash == account_hash))
        if status:
            stmt = stmt.where(Subscription.status == status)
        if interval:
            stmt = stmt.where(Subscription.billing_interval == interval)
        if category:
            stmt = stmt.where(Subscription.category_key == category)
        if group_id:
            stmt = stmt.where(Subscription.group_id == group_id)
        total = self.session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
        items = self.session.scalars(stmt.order_by(Subscription.renewal_date.is_(None), Subscription.renewal_date.asc(), Subscription.name.asc()).offset(offset).limit(limit)).all()
        return items, total

    def get(self, owner_subject_id: str, subscription_id: UUID) -> Subscription:
        item = self.session.get(Subscription, subscription_id)
        if item is None or item.owner_subject_id != owner_subject_id or item.deleted_at is not None:
            raise NotFoundError("Subscription not found")
        return item

    def update(self, owner_subject_id: str, actor_subject_id: str, subscription_id: UUID, payload: SubscriptionUpdate) -> Subscription:
        item = self.get(owner_subject_id, subscription_id)
        data = payload.model_dump(exclude_unset=True)
        if "group_id" in data:
            group = self._validate_group(owner_subject_id, data["group_id"])
            item.group_id = data["group_id"]
            if group:
                item.amount_model = "group_child"
                item.amount_minor = None
                item.renewal_date = group.renewal_date
                item.billing_interval = group.billing_interval
        for field in ["name", "service_url", "category_key", "status", "billing_interval", "amount_minor", "amount_model", "estimate_strategy", "estimate_confidence", "renewal_date", "trial_end_date", "notes"]:
            if field in data and not (field in {"amount_minor", "amount_model", "renewal_date", "billing_interval"} and item.group_id):
                setattr(item, field, data[field].strip() if isinstance(data[field], str) and field == "name" else data[field])
        if "account_identifier" in data:
            self._apply_account(item, data["account_identifier"])
        item.updated_at = datetime.now(timezone.utc)
        self._write_price_history(item, actor_subject_id)
        self._sync(item)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="subscription_updated", target_type="subscription", target_id=str(item.id), payload={"changed_fields": list(data.keys())})
        self.session.commit()
        self.session.refresh(item)
        return item

    def soft_delete(self, owner_subject_id: str, actor_subject_id: str, subscription_id: UUID) -> None:
        item = self.get(owner_subject_id, subscription_id)
        item.deleted_at = datetime.now(timezone.utc)
        item.status = "archived"
        self._sync(item)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="subscription_deleted", target_type="subscription", target_id=str(item.id))
        self.session.commit()

    def move_to_group(self, owner_subject_id: str, actor_subject_id: str, subscription_id: UUID, group_id: UUID) -> Subscription:
        item = self.get(owner_subject_id, subscription_id)
        group = self._validate_group(owner_subject_id, group_id)
        assert group is not None
        item.group_id = group.id
        item.amount_model = "group_child"
        item.amount_minor = None
        item.billing_interval = group.billing_interval
        item.renewal_date = group.renewal_date
        self._sync(item)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="moved_to_group", target_type="subscription", target_id=str(item.id), payload={"group_id": str(group_id)})
        self.session.commit()
        self.session.refresh(item)
        return item

    def record_payment(self, owner_subject_id: str, actor_subject_id: str, subscription_id: UUID, payload: PaymentCreate) -> PaymentRecord:
        item = self.get(owner_subject_id, subscription_id)
        paid_at = payload.paid_at or datetime.now(timezone.utc)
        payment = PaymentRecord(owner_subject_id=owner_subject_id, occurrence_id=payload.occurrence_id, source_type="subscription", source_id=item.id, amount_minor=payload.amount_minor, paid_at=paid_at, note=payload.note)
        item.last_paid_amount_minor = payload.amount_minor
        item.last_paid_at = paid_at
        if payload.occurrence_id:
            occ = self.session.get(BillingOccurrence, payload.occurrence_id)
            if occ and occ.owner_subject_id == owner_subject_id:
                occ.status = "paid"
        self.session.add(payment)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="payment_recorded", target_type="subscription", target_id=str(item.id), payload={"amount_minor": payload.amount_minor})
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def _write_price_history(self, item: Subscription, actor_subject_id: str) -> None:
        if item.amount_minor is not None:
            self.session.add(SubscriptionPriceHistory(subscription_id=item.id, amount_minor=item.amount_minor, currency=item.currency, billing_interval=item.billing_interval, changed_by_subject_id=actor_subject_id, source="user"))

    def _sync(self, item: Subscription) -> None:
        if item.group_id is not None:
            item.calendar_sync_status = "not_synced"
            item.calendar_sync_error = None
            return
        item.calendar_external_ref = item.calendar_external_ref or f"subs:subscription:{item.id}"
        try:
            event_id, status, error = CalendarSyncService().sync_subscription(item)
            item.calendar_event_id = event_id
            item.calendar_sync_status = status
            item.calendar_sync_error = error
        except Exception as exc:
            item.calendar_sync_status = "failed"
            item.calendar_sync_error = str(exc)[:500]
