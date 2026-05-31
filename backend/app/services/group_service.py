from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationAppError
from app.models.entities import BillingOccurrence, PaymentRecord, Subscription, SubscriptionGroup, SubscriptionPriceHistory
from app.schemas.common import PaymentCreate
from app.schemas.group import GroupCreate, GroupUpdate, RemoveSubscriptionPayload
from app.services.audit import write_audit
from app.services.calendar_sync_service import CalendarSyncService


class GroupService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, owner_subject_id: str, actor_subject_id: str, payload: GroupCreate) -> SubscriptionGroup:
        item = SubscriptionGroup(owner_subject_id=owner_subject_id, created_by_subject_id=actor_subject_id, **payload.model_dump())
        self.session.add(item)
        self.session.flush()
        self._write_price_history(item, actor_subject_id)
        self._sync(item)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="group_created", target_type="group", target_id=str(item.id), payload={"name": item.name})
        self.session.commit()
        self.session.refresh(item)
        return item

    def list(self, owner_subject_id: str, q: str | None = None, limit: int = 100, offset: int = 0):
        stmt = select(SubscriptionGroup).where(SubscriptionGroup.owner_subject_id == owner_subject_id, SubscriptionGroup.deleted_at.is_(None))
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(or_(SubscriptionGroup.name.ilike(pattern), SubscriptionGroup.service_url.ilike(pattern)))
        items = self.session.scalars(stmt.order_by(SubscriptionGroup.renewal_date.is_(None), SubscriptionGroup.renewal_date.asc(), SubscriptionGroup.name.asc()).offset(offset).limit(limit)).all()
        total = len(self.session.scalars(select(SubscriptionGroup).where(SubscriptionGroup.owner_subject_id == owner_subject_id, SubscriptionGroup.deleted_at.is_(None))).all())
        return items, total

    def get(self, owner_subject_id: str, group_id: UUID) -> SubscriptionGroup:
        item = self.session.get(SubscriptionGroup, group_id)
        if item is None or item.owner_subject_id != owner_subject_id or item.deleted_at is not None:
            raise NotFoundError("Group not found")
        return item

    def update(self, owner_subject_id: str, actor_subject_id: str, group_id: UUID, payload: GroupUpdate) -> SubscriptionGroup:
        item = self.get(owner_subject_id, group_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(item, field, value.strip() if isinstance(value, str) and field == "name" else value)
        item.updated_at = datetime.now(timezone.utc)
        for child in item.subscriptions:
            if child.deleted_at is None and child.amount_model == "group_child":
                child.billing_interval = item.billing_interval
                child.renewal_date = item.renewal_date
        self._write_price_history(item, actor_subject_id)
        self._sync(item)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="group_updated", target_type="group", target_id=str(item.id), payload={"changed_fields": list(data.keys())})
        self.session.commit()
        self.session.refresh(item)
        return item

    def soft_delete(self, owner_subject_id: str, actor_subject_id: str, group_id: UUID, detach_children: bool = False) -> None:
        item = self.get(owner_subject_id, group_id)
        active_children = [child for child in item.subscriptions if child.deleted_at is None]
        if active_children and not detach_children:
            raise ValidationAppError("Group has active subscriptions", details={"children": len(active_children), "required": "detach_children=true"})
        for child in active_children:
            child.group_id = None
            child.amount_model = "unknown"
            child.amount_minor = None
        item.deleted_at = datetime.now(timezone.utc)
        item.status = "archived"
        self._sync(item)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="group_deleted", target_type="group", target_id=str(item.id))
        self.session.commit()

    def add_subscription(self, owner_subject_id: str, actor_subject_id: str, group_id: UUID, subscription_id: UUID) -> Subscription:
        group = self.get(owner_subject_id, group_id)
        sub = self.session.get(Subscription, subscription_id)
        if sub is None or sub.owner_subject_id != owner_subject_id or sub.deleted_at is not None:
            raise NotFoundError("Subscription not found")
        sub.group_id = group.id
        sub.amount_model = "group_child"
        sub.amount_minor = None
        sub.billing_interval = group.billing_interval
        sub.renewal_date = group.renewal_date
        self._sync(group)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="moved_to_group", target_type="subscription", target_id=str(sub.id), payload={"group_id": str(group.id)})
        self.session.commit()
        self.session.refresh(sub)
        return sub

    def remove_subscription(self, owner_subject_id: str, actor_subject_id: str, group_id: UUID, subscription_id: UUID, payload: RemoveSubscriptionPayload) -> Subscription:
        group = self.get(owner_subject_id, group_id)
        sub = self.session.get(Subscription, subscription_id)
        if sub is None or sub.owner_subject_id != owner_subject_id or sub.group_id != group.id or sub.deleted_at is not None:
            raise NotFoundError("Subscription not found")
        if payload.amount_model == "fixed" and payload.amount_minor is None:
            raise ValidationAppError("amount_minor is required when removing subscription from group")
        sub.group_id = None
        sub.amount_model = payload.amount_model
        sub.amount_minor = payload.amount_minor
        sub.billing_interval = payload.billing_interval
        sub.renewal_date = payload.renewal_date or group.renewal_date
        self._sync(group)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="removed_from_group", target_type="subscription", target_id=str(sub.id), payload={"group_id": str(group.id)})
        self.session.commit()
        self.session.refresh(sub)
        return sub

    def record_payment(self, owner_subject_id: str, actor_subject_id: str, group_id: UUID, payload: PaymentCreate) -> PaymentRecord:
        item = self.get(owner_subject_id, group_id)
        paid_at = payload.paid_at or datetime.now(timezone.utc)
        payment = PaymentRecord(owner_subject_id=owner_subject_id, occurrence_id=payload.occurrence_id, source_type="group", source_id=item.id, amount_minor=payload.amount_minor, paid_at=paid_at, note=payload.note)
        item.last_paid_amount_minor = payload.amount_minor
        item.last_paid_at = paid_at
        if payload.occurrence_id:
            occ = self.session.get(BillingOccurrence, payload.occurrence_id)
            if occ and occ.owner_subject_id == owner_subject_id:
                occ.status = "paid"
        self.session.add(payment)
        write_audit(self.session, owner_subject_id=owner_subject_id, actor_subject_id=actor_subject_id, action="payment_recorded", target_type="group", target_id=str(item.id), payload={"amount_minor": payload.amount_minor})
        self.session.commit()
        self.session.refresh(payment)
        return payment

    def _write_price_history(self, item: SubscriptionGroup, actor_subject_id: str) -> None:
        if item.amount_minor is not None:
            self.session.add(SubscriptionPriceHistory(group_id=item.id, amount_minor=item.amount_minor, currency=item.currency, billing_interval=item.billing_interval, changed_by_subject_id=actor_subject_id, source="user"))

    def _sync(self, item: SubscriptionGroup) -> None:
        item.calendar_external_ref = item.calendar_external_ref or f"subs:group:{item.id}"
        try:
            event_id, status, error = CalendarSyncService().sync_group(item)
            item.calendar_event_id = event_id
            item.calendar_sync_status = status
            item.calendar_sync_error = error
        except Exception as exc:
            item.calendar_sync_status = "failed"
            item.calendar_sync_error = str(exc)[:500]
