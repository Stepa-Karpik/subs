from collections import defaultdict
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.errors import NotFoundError
from app.core.responses import success_response
from app.models.entities import Subscription, SubscriptionGroup, SubscriptionRecommendation
from app.schemas.recommendation import RecommendationRead
from app.services.billing_calculator import normalize_amount

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

def _create_rec(session, owner, target_type, target_id, type_, severity, confidence, title, explanation, saving=None):
    existing = session.scalar(select(SubscriptionRecommendation).where(SubscriptionRecommendation.owner_subject_id == owner, SubscriptionRecommendation.target_type == target_type, SubscriptionRecommendation.target_id == target_id, SubscriptionRecommendation.type == type_))
    if existing:
        return existing
    rec = SubscriptionRecommendation(owner_subject_id=owner, target_type=target_type, target_id=target_id, type=type_, severity=severity, confidence=confidence, title=title, explanation=explanation, estimated_saving_minor=saving)
    session.add(rec)
    return rec

def _run_analysis(session: Session, owner: str) -> None:
    subs = session.scalars(select(Subscription).where(Subscription.owner_subject_id == owner, Subscription.deleted_at.is_(None), Subscription.status.in_(["active", "trial"]))).all()
    by_category = defaultdict(list)
    today = date.today()
    for sub in subs:
        if sub.category_key:
            by_category[sub.category_key].append(sub)
        if not sub.renewal_date or sub.amount_model == "unknown":
            _create_rec(session, owner, "subscription", sub.id, "missing_data", "warning", 0.92, "Нужно заполнить данные", f"В подписке «{sub.name}» не хватает даты или суммы для точного прогноза.")
        if sub.amount_model == "variable" and sub.estimate_confidence == "low":
            _create_rec(session, owner, "subscription", sub.id, "missing_data", "info", 0.72, "Уточните прогноз", f"«{sub.name}» считается по примерной сумме. После оплаты отметьте фактическую сумму.")
        trial_date = sub.trial_end_date or (sub.renewal_date if sub.status == "trial" else None)
        if trial_date and today <= trial_date <= today + timedelta(days=7):
            norm = normalize_amount(sub.amount_minor, sub.billing_interval, sub.amount_model)
            _create_rec(session, owner, "subscription", sub.id, "upcoming_trial_end", "important", 0.8, "Заканчивается пробный период", f"У «{sub.name}» заканчивается пробный период или доступ в ближайшие 7 дней.", norm.yearly_minor)
    for category, items in by_category.items():
        paid = [item for item in items if item.amount_model not in {"free", "group_child", "unknown"}]
        if len(paid) > 1:
            names = ", ".join(item.name for item in paid[:3])
            _create_rec(session, owner, "subscription", paid[0].id, "duplicate", "warning", 0.7, "Похожие подписки", f"В категории «{category}» есть несколько активных подписок: {names}. Проверьте, нужны ли все.")
    groups = session.scalars(select(SubscriptionGroup).where(SubscriptionGroup.owner_subject_id == owner, SubscriptionGroup.deleted_at.is_(None), SubscriptionGroup.status == "active")).all()
    for group in groups:
        if not group.subscriptions:
            _create_rec(session, owner, "group", group.id, "group_inefficient", "info", 0.6, "Пустая группа", f"В группе «{group.name}» пока нет подписок, но цена учитывается в прогнозе.", group.amount_minor)

@router.get("")
def list_recommendations(request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    items = session.scalars(select(SubscriptionRecommendation).where(SubscriptionRecommendation.owner_subject_id == current_user.user_id, SubscriptionRecommendation.status == "active").order_by(SubscriptionRecommendation.created_at.desc())).all()
    return success_response(data=[RecommendationRead.model_validate(item).model_dump(mode="json") for item in items], request=request)

@router.post("/run")
def run_recommendations(request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    owner = current_user.user_id
    _run_analysis(session, owner)
    session.commit()
    return list_recommendations(request, current_user, session)

@router.post("/{recommendation_id}/dismiss")
def dismiss(recommendation_id, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = session.get(SubscriptionRecommendation, recommendation_id)
    if item is None or item.owner_subject_id != current_user.user_id:
        raise NotFoundError("Recommendation not found")
    item.status = "dismissed"
    session.commit()
    return success_response(data=RecommendationRead.model_validate(item).model_dump(mode="json"), request=request)

@router.post("/{recommendation_id}/mark-checked")
def mark_checked(recommendation_id, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = session.get(SubscriptionRecommendation, recommendation_id)
    if item is None or item.owner_subject_id != current_user.user_id:
        raise NotFoundError("Recommendation not found")
    item.status = "checked"
    session.commit()
    return success_response(data=RecommendationRead.model_validate(item).model_dump(mode="json"), request=request)
