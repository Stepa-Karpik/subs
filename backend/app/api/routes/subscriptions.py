from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.responses import success_response
from app.schemas.common import PaymentCreate, PaymentRead
from app.schemas.subscription import MoveToGroupPayload, SubscriptionCreate, SubscriptionRead, SubscriptionUpdate
from app.services.serializers import subscription_to_dict
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("")
def list_subscriptions(request: Request, q: str | None = None, status_filter: str | None = Query(default=None, alias="status"), interval: str | None = None, category: str | None = None, group_id: UUID | None = None, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    items, total = SubscriptionService(session).list(current_user.user_id, q=q, status=status_filter, interval=interval, category=category, group_id=group_id, limit=limit, offset=offset)
    return success_response(data=[SubscriptionRead.model_validate(subscription_to_dict(item)).model_dump(mode="json") for item in items], request=request, pagination={"limit": limit, "offset": offset, "total": total})

@router.post("", status_code=status.HTTP_201_CREATED)
def create_subscription(payload: SubscriptionCreate, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = SubscriptionService(session).create(current_user.user_id, current_user.user_id, payload)
    return success_response(data=SubscriptionRead.model_validate(subscription_to_dict(item)).model_dump(mode="json"), request=request)

@router.get("/{subscription_id}")
def get_subscription(subscription_id: UUID, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = SubscriptionService(session).get(current_user.user_id, subscription_id)
    return success_response(data=SubscriptionRead.model_validate(subscription_to_dict(item)).model_dump(mode="json"), request=request)

@router.patch("/{subscription_id}")
def update_subscription(subscription_id: UUID, payload: SubscriptionUpdate, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = SubscriptionService(session).update(current_user.user_id, current_user.user_id, subscription_id, payload)
    return success_response(data=SubscriptionRead.model_validate(subscription_to_dict(item)).model_dump(mode="json"), request=request)

@router.delete("/{subscription_id}")
def delete_subscription(subscription_id: UUID, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    SubscriptionService(session).soft_delete(current_user.user_id, current_user.user_id, subscription_id)
    return success_response(data={"ok": True}, request=request)

@router.post("/{subscription_id}/move-to-group")
def move_to_group(subscription_id: UUID, payload: MoveToGroupPayload, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = SubscriptionService(session).move_to_group(current_user.user_id, current_user.user_id, subscription_id, payload.group_id)
    return success_response(data=SubscriptionRead.model_validate(subscription_to_dict(item)).model_dump(mode="json"), request=request)

@router.post("/{subscription_id}/payments", status_code=status.HTTP_201_CREATED)
def record_payment(subscription_id: UUID, payload: PaymentCreate, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = SubscriptionService(session).record_payment(current_user.user_id, current_user.user_id, subscription_id, payload)
    return success_response(data=PaymentRead.model_validate(item).model_dump(mode="json"), request=request)
