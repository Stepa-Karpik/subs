from __future__ import annotations

from app.core.config import get_settings
from app.core.security import decrypt_text, mask_identifier
from app.models.entities import Subscription, SubscriptionGroup
from app.services.billing_calculator import normalize_amount


def subscription_to_dict(item: Subscription) -> dict:
    settings = get_settings()
    normalized = normalize_amount(item.amount_minor, item.billing_interval, item.amount_model)
    identifier = decrypt_text(item.account_identifier_encrypted, settings.account_identifier_encryption_key)
    return {
        "id": item.id,
        "group_id": item.group_id,
        "name": item.name,
        "service_url": item.service_url,
        "account_identifier_masked": mask_identifier(identifier),
        "category_key": item.category_key,
        "status": item.status,
        "billing_interval": item.billing_interval,
        "amount_minor": item.amount_minor,
        "amount_model": item.amount_model,
        "estimate_strategy": item.estimate_strategy,
        "estimate_confidence": item.estimate_confidence,
        "currency": item.currency,
        "renewal_date": item.renewal_date,
        "trial_end_date": item.trial_end_date,
        "calendar_event_id": item.calendar_event_id,
        "calendar_external_ref": item.calendar_external_ref,
        "calendar_sync_status": item.calendar_sync_status,
        "calendar_sync_error": item.calendar_sync_error,
        "last_paid_amount_minor": item.last_paid_amount_minor,
        "last_paid_at": item.last_paid_at,
        "notes": item.notes,
        "monthly_minor": normalized.monthly_minor,
        "yearly_minor": normalized.yearly_minor,
        "is_estimated": normalized.is_estimated,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "deleted_at": item.deleted_at,
    }


def group_to_dict(item: SubscriptionGroup, include_children: bool = True) -> dict:
    normalized = normalize_amount(item.amount_minor, item.billing_interval, item.amount_model)
    return {
        "id": item.id,
        "name": item.name,
        "service_url": item.service_url,
        "status": item.status,
        "billing_interval": item.billing_interval,
        "amount_minor": item.amount_minor,
        "amount_model": item.amount_model,
        "estimate_strategy": item.estimate_strategy,
        "estimate_confidence": item.estimate_confidence,
        "currency": item.currency,
        "renewal_date": item.renewal_date,
        "calendar_event_id": item.calendar_event_id,
        "calendar_external_ref": item.calendar_external_ref,
        "calendar_sync_status": item.calendar_sync_status,
        "calendar_sync_error": item.calendar_sync_error,
        "last_paid_amount_minor": item.last_paid_amount_minor,
        "last_paid_at": item.last_paid_at,
        "notes": item.notes,
        "monthly_minor": normalized.monthly_minor,
        "yearly_minor": normalized.yearly_minor,
        "is_estimated": normalized.is_estimated,
        "subscriptions": [subscription_to_dict(sub) for sub in item.subscriptions if sub.deleted_at is None] if include_children else [],
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "deleted_at": item.deleted_at,
    }
