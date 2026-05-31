from datetime import date, datetime, timezone
from app.models.entities import PaymentRecord
from app.schemas.subscription import SubscriptionCreate
from app.services.subscription_service import SubscriptionService
from app.services.variable_estimate_service import VariableEstimateService
from app.services.forecast_service import ForecastService


def test_variable_subscription_uses_estimated_marker(session):
    sub = SubscriptionService(session).create("usr", "usr", SubscriptionCreate(name="ЖКХ", category_key="utilities", amount_minor=6400_00, amount_model="variable", billing_interval="monthly", renewal_date=date(2026, 6, 10), estimate_strategy="manual_estimate", estimate_confidence="medium"))
    summary = ForecastService(session).dashboard("usr", month=date(2026, 6, 1))
    assert sub.amount_model == "variable"
    assert summary["variable_estimated_minor"] == 6400_00


def test_variable_estimate_uses_payment_history(session):
    service = SubscriptionService(session)
    sub = service.create("usr", "usr", SubscriptionCreate(name="Электричество", category_key="electricity", amount_minor=1000_00, amount_model="variable", billing_interval="monthly", renewal_date=date(2026, 6, 10)))
    session.add(PaymentRecord(owner_subject_id="usr", source_type="subscription", source_id=sub.id, amount_minor=1200_00, paid_at=datetime(2026, 4, 10, tzinfo=timezone.utc)))
    session.add(PaymentRecord(owner_subject_id="usr", source_type="subscription", source_id=sub.id, amount_minor=1800_00, paid_at=datetime(2026, 5, 10, tzinfo=timezone.utc)))
    session.commit()
    estimate = VariableEstimateService(session).estimate(owner_subject_id="usr", source_type="subscription", source_id=sub.id, category_key="electricity")
    assert estimate.amount_minor == 1500_00
    assert estimate.strategy == "user_history_avg"
