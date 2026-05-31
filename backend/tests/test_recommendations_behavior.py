from datetime import date, timedelta

from app.api.routes.recommendations import _run_analysis
from app.models.entities import Subscription, SubscriptionRecommendation


def _sub(session, name: str, **overrides):
    item = Subscription(
        owner_subject_id="usr",
        created_by_subject_id="usr",
        name=name,
        status="active",
        billing_interval="monthly",
        amount_minor=499_00,
        amount_model="fixed",
        category_key="media",
        renewal_date=date.today(),
    )
    for key, value in overrides.items():
        setattr(item, key, value)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def test_checked_recommendation_is_not_recreated_on_next_analysis(session):
    _sub(session, "Netflix", amount_minor=None, amount_model="unknown", renewal_date=None)

    _run_analysis(session, "usr")
    recs = session.query(SubscriptionRecommendation).all()
    assert len(recs) == 1

    recs[0].status = "checked"
    session.commit()

    _run_analysis(session, "usr")
    all_recs = session.query(SubscriptionRecommendation).all()
    assert len(all_recs) == 1
    assert all_recs[0].status == "checked"


def test_normal_renewal_in_next_seven_days_is_not_recommended_without_trial_or_end_date(session):
    _sub(session, "Regular cloud", renewal_date=date.today() + timedelta(days=2))

    _run_analysis(session, "usr")

    assert session.query(SubscriptionRecommendation).all() == []


def test_trial_ending_in_next_seven_days_is_recommended(session):
    _sub(
        session,
        "Trial service",
        status="trial",
        renewal_date=date.today() + timedelta(days=2),
        trial_end_date=date.today() + timedelta(days=2),
    )

    _run_analysis(session, "usr")

    assert [item.type for item in session.query(SubscriptionRecommendation).all()] == ["upcoming_trial_end"]
