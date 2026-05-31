from __future__ import annotations

from app.models.entities import Subscription, SubscriptionGroup
from app.services.billing_calculator import next_occurrence_dates, normalize_amount
from app.services.planner_client import PlannerClient, PlannerSubscriptionEventPayload, renewal_datetime

ACTIVE_STATUSES = {"active", "trial"}
SYNC_MONTHS_AHEAD = 12


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
        base_ref = item.calendar_external_ref or f"subs:subscription:{item.id}"
        if item.deleted_at or item.status not in ACTIVE_STATUSES:
            self.client.delete_subscription_events_by_prefix(base_ref)
            if item.calendar_external_ref:
                self.client.delete_subscription_event(item.calendar_external_ref)
            return item.calendar_event_id, "deleted", None
        if not item.renewal_date:
            return item.calendar_event_id, "not_synced", "renewal_date_missing"
        self.client.delete_subscription_events_by_prefix(base_ref)
        normalized = normalize_amount(item.amount_minor, item.billing_interval, item.amount_model)
        price = format_price(item.amount_minor, normalized.is_estimated)
        account = ""
        if item.account_identifier_encrypted:
            account = " Аккаунт указан."
        description = f"{price} / {item.billing_interval}.{account}"
        first_event_id = item.calendar_event_id
        for idx, starts_on in enumerate(next_occurrence_dates(item.renewal_date, item.billing_interval, months_ahead=SYNC_MONTHS_AHEAD)):
            payload = PlannerSubscriptionEventPayload(
                owner_subject_id=item.owner_subject_id,
                external_ref=f"{base_ref}:{starts_on.isoformat()}",
                title=f"Оплата: {item.name}",
                description=description,
                starts_at=renewal_datetime(starts_on, item.timezone),
                details_url=f"https://subs.nerior.ru/subscriptions?subscription={item.id}",
            )
            event_id = self.client.upsert_subscription_event(payload)
            if idx == 0 and event_id:
                first_event_id = event_id
        return first_event_id, "synced", None

    def sync_group(self, item: SubscriptionGroup) -> tuple[str | None, str, str | None]:
        base_ref = item.calendar_external_ref or f"subs:group:{item.id}"
        if item.deleted_at or item.status not in ACTIVE_STATUSES:
            self.client.delete_subscription_events_by_prefix(base_ref)
            if item.calendar_external_ref:
                self.client.delete_subscription_event(item.calendar_external_ref)
            return item.calendar_event_id, "deleted", None
        if not item.renewal_date:
            return item.calendar_event_id, "not_synced", "renewal_date_missing"
        self.client.delete_subscription_events_by_prefix(base_ref)
        normalized = normalize_amount(item.amount_minor, item.billing_interval, item.amount_model)
        price = format_price(item.amount_minor, normalized.is_estimated)
        children = ", ".join(sub.name for sub in item.subscriptions if sub.deleted_at is None) or "нет вложенных подписок"
        first_event_id = item.calendar_event_id
        for idx, starts_on in enumerate(next_occurrence_dates(item.renewal_date, item.billing_interval, months_ahead=SYNC_MONTHS_AHEAD)):
            payload = PlannerSubscriptionEventPayload(
                owner_subject_id=item.owner_subject_id,
                external_ref=f"{base_ref}:{starts_on.isoformat()}",
                title=f"Оплата группы: {item.name}",
                description=f"{price} / {item.billing_interval}. В составе: {children}",
                starts_at=renewal_datetime(starts_on, item.timezone),
                details_url=f"https://subs.nerior.ru/groups?group={item.id}",
            )
            event_id = self.client.upsert_subscription_event(payload)
            if idx == 0 and event_id:
                first_event_id = event_id
        return first_event_id, "synced", None
