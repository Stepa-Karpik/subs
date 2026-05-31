from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.responses import success_response
from app.models.entities import Subscription, SubscriptionGroup
from app.schemas.integration import IntegrationStatus
from app.services.audit import write_audit
from app.services.group_service import GroupService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/integrations", tags=["Integrations"])

@router.get("/status")
def status(request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    failed = session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == current_user.user_id, Subscription.calendar_sync_status == "failed")) or 0
    failed += session.scalar(select(func.count(SubscriptionGroup.id)).where(SubscriptionGroup.owner_subject_id == current_user.user_id, SubscriptionGroup.calendar_sync_status == "failed")) or 0
    pending = session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == current_user.user_id, Subscription.calendar_sync_status.in_(["pending", "not_synced"]))) or 0
    synced = session.scalar(select(func.count(Subscription.id)).where(Subscription.owner_subject_id == current_user.user_id, Subscription.calendar_sync_status == "synced")) or 0
    return success_response(data=IntegrationStatus(failed_sync_count=failed, pending_sync_count=pending, synced_count=synced).model_dump(), request=request)


@router.post("/sync-now")
def sync_now(request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    sub_service = SubscriptionService(session)
    group_service = GroupService(session)
    subscriptions = session.scalars(
        select(Subscription).where(
            Subscription.owner_subject_id == current_user.user_id,
            Subscription.deleted_at.is_(None),
            Subscription.group_id.is_(None),
            Subscription.calendar_sync_status.in_(["failed", "pending", "not_synced"]),
        )
    ).all()
    groups = session.scalars(
        select(SubscriptionGroup).where(
            SubscriptionGroup.owner_subject_id == current_user.user_id,
            SubscriptionGroup.deleted_at.is_(None),
            SubscriptionGroup.calendar_sync_status.in_(["failed", "pending", "not_synced"]),
        )
    ).all()
    for item in subscriptions:
        sub_service._sync(item)
    for item in groups:
        group_service._sync(item)
    write_audit(
        session,
        owner_subject_id=current_user.user_id,
        actor_subject_id=current_user.user_id,
        action="calendar_sync_requested",
        target_type="integration",
        target_id="planner",
        payload={"subscriptions": len(subscriptions), "groups": len(groups)},
    )
    session.commit()
    return success_response(data={"subscriptions": len(subscriptions), "groups": len(groups)}, request=request)
