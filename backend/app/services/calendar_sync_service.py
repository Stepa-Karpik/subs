from __future__ import annotations

from app.models.entities import Subscription, SubscriptionGroup
from app.services.billing_calculator import normalize_amount
from app.services.planner_client import PlannerClient, PlannerSubscriptionEventPayload, renewal_datetime


def format_price(amount_minor: int | None, estimated: bool = False) -> str:
    if amount_minor is None:
        return "сумма не указана"
    rub = amount_minor / 100
    text = f"{rub:,.0f} ₽".replace(",", " ")
    return f"≈ {text}" if estimated else text


class CalendarSyncService:
    def __init__(self) -> None:
        self.client = PlannerClient()

    def sync_subscription(self, item: Subscription) -> tuple[str | None, str, str | None]:
        if item.deleted_at or item.status in {"cancelled", "paused", "expired", "archived"}:
            if item.calendar_external_ref:
                self.client.delete_subscription_event(item.calendar_external_ref)
            return item.calendar_event_id, "deleted", None
        if not item.renewal_date:
            return item.calendar_event_id, "not_synced", "renewal_date_missing"
        external_ref = item.calendar_external_ref or f"subs:subscription:{item.id}"
        normalized = normalize_amount(item.amount_minor, item.billing_interval, item.amount_model)
        price = format_price(item.amount_minor, normalized.is_estimated)
        account = ""
        if item.account_identifier_encrypted:
            account = " Аккаунт указан."
        description = f"{price} / {item.billing_interval}.{account}"
        payload = PlannerSubscriptionEventPayload(
            owner_subject_id=item.owner_subject_id,
            external_ref=external_ref,
            title=f"Оплата: {item.name}",
            description=description,
            starts_at=renewal_datetime(item.renewal_date, item.timezone),
        )
        event_id = self.client.upsert_subscription_event(payload)
        return event_id or item.calendar_event_id, "synced", None

    def sync_group(self, item: SubscriptionGroup) -> tuple[str | None, str, str | None]:
        if item.deleted_at or item.status in {"cancelled", "paused", "expired", "archived"}:
            if item.calendar_external_ref:
                self.client.delete_subscription_event(item.calendar_external_ref)
            return item.calendar_event_id, "deleted", None
        if not item.renewal_date:
            return item.calendar_event_id, "not_synced", "renewal_date_missing"
        external_ref = item.calendar_external_ref or f"subs:group:{item.id}"
        normalized = normalize_amount(item.amount_minor, item.billing_interval, item.amount_model)
        price = format_price(item.amount_minor, normalized.is_estimated)
        children = ", ".join(sub.name for sub in item.subscriptions if sub.deleted_at is None) or "нет вложенных подписок"
        payload = PlannerSubscriptionEventPayload(
            owner_subject_id=item.owner_subject_id,
            external_ref=external_ref,
            title=f"Оплата группы: {item.name}",
            description=f"{price} / {item.billing_interval}. В составе: {children}",
            starts_at=renewal_datetime(item.renewal_date, item.timezone),
        )
        event_id = self.client.upsert_subscription_event(payload)
        return event_id or item.calendar_event_id, "synced", None
