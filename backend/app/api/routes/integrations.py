from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.responses import success_response
from app.models.entities import Subscription, SubscriptionGroup
from app.schemas.integration import IntegrationStatus

router = APIRouter(prefix="/integrations", tags=["Integrations"])

@router.get("/status")
def status(request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    failed = session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == current_user.user_id, Subscription.calendar_sync_status == "failed")) or 0
    failed += session.scalar(select(func.count(SubscriptionGroup.id)).where(SubscriptionGroup.owner_subject_id == current_user.user_id, SubscriptionGroup.calendar_sync_status == "failed")) or 0
    pending = session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == current_user.user_id, Subscription.calendar_sync_status.in_(["pending", "not_synced"]))) or 0
    synced = session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == current_user.user_id, Subscription.calendar_sync_status == "synced")) or 0
    return success_response(data=IntegrationStatus(failed_sync_count=failed, pending_sync_count=pending, synced_count=synced).model_dump(), request=request)
