from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.errors import ForbiddenError
from app.core.responses import success_response
from app.models.entities import Subscription, SubscriptionGroup, SubscriptionRecommendation

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/stats")
def stats(request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    if not current_user.is_platform_admin:
        raise ForbiddenError("Admin access required")
    active_subs = session.scalar(select(func.count(Subscription.id)).where(Subscription.deleted_at.is_(None), Subscription.status.in_(["active", "trial"]))) or 0
    active_groups = session.scalar(select(func.count(SubscriptionGroup.id)).where(SubscriptionGroup.deleted_at.is_(None), SubscriptionGroup.status == "active")) or 0
    failed = session.scalar(select(func.count(Subscription.id)).where(Subscription.calendar_sync_status == "failed")) or 0
    recs = session.scalar(select(func.count(SubscriptionRecommendation.id)).where(SubscriptionRecommendation.status == "active")) or 0
    return success_response(data={"service": "subs", "active_subscriptions": active_subs, "active_groups": active_groups, "calendar_sync_failed": failed, "recommendations_active": recs}, request=request)
