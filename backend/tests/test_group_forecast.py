from datetime import date
from app.schemas.group import GroupCreate
from app.schemas.subscription import SubscriptionCreate
from app.services.forecast_service import ForecastService
from app.services.group_service import GroupService
from app.services.subscription_service import SubscriptionService


def test_group_children_are_not_double_counted(session):
    group = GroupService(session).create("usr", "usr", GroupCreate(name="MIXX", amount_minor=999_00, billing_interval="monthly", renewal_date=date(2026, 6, 15)))
    sub = SubscriptionService(session).create("usr", "usr", SubscriptionCreate(name="Музыка", amount_minor=299_00, billing_interval="monthly", renewal_date=date(2026, 6, 15), group_id=group.id))
    summary = ForecastService(session).summary("usr")
    assert sub.amount_model == "group_child"
    assert summary["monthly_total_minor"] == 999_00
