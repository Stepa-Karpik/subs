from uuid import UUID
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.responses import success_response
from app.schemas.common import PaymentCreate, PaymentRead
from app.schemas.group import AddSubscriptionPayload, GroupCreate, GroupRead, GroupUpdate, RemoveSubscriptionPayload
from app.schemas.subscription import SubscriptionRead
from app.services.group_service import GroupService
from app.services.serializers import group_to_dict, subscription_to_dict

router = APIRouter(prefix="/groups", tags=["Groups"])

@router.get("")
def list_groups(request: Request, q: str | None = None, limit: int = Query(default=100, ge=1, le=500), offset: int = Query(default=0, ge=0), current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    items, total = GroupService(session).list(current_user.user_id, q=q, limit=limit, offset=offset)
    return success_response(data=[GroupRead.model_validate(group_to_dict(item)).model_dump(mode="json") for item in items], request=request, pagination={"limit": limit, "offset": offset, "total": total})

@router.post("", status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupCreate, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = GroupService(session).create(current_user.user_id, current_user.user_id, payload)
    return success_response(data=GroupRead.model_validate(group_to_dict(item)).model_dump(mode="json"), request=request)

@router.get("/{group_id}")
def get_group(group_id: UUID, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = GroupService(session).get(current_user.user_id, group_id)
    return success_response(data=GroupRead.model_validate(group_to_dict(item)).model_dump(mode="json"), request=request)

@router.patch("/{group_id}")
def update_group(group_id: UUID, payload: GroupUpdate, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = GroupService(session).update(current_user.user_id, current_user.user_id, group_id, payload)
    return success_response(data=GroupRead.model_validate(group_to_dict(item)).model_dump(mode="json"), request=request)

@router.delete("/{group_id}")
def delete_group(group_id: UUID, request: Request, detach_children: bool = False, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    GroupService(session).soft_delete(current_user.user_id, current_user.user_id, group_id, detach_children=detach_children)
    return success_response(data={"ok": True}, request=request)

@router.post("/{group_id}/add-subscription")
def add_subscription(group_id: UUID, payload: AddSubscriptionPayload, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = GroupService(session).add_subscription(current_user.user_id, current_user.user_id, group_id, payload.subscription_id)
    return success_response(data=SubscriptionRead.model_validate(subscription_to_dict(item)).model_dump(mode="json"), request=request)

@router.post("/{group_id}/remove-subscription/{subscription_id}")
def remove_subscription(group_id: UUID, subscription_id: UUID, payload: RemoveSubscriptionPayload, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = GroupService(session).remove_subscription(current_user.user_id, current_user.user_id, group_id, subscription_id, payload)
    return success_response(data=SubscriptionRead.model_validate(subscription_to_dict(item)).model_dump(mode="json"), request=request)

@router.post("/{group_id}/payments", status_code=status.HTTP_201_CREATED)
def record_payment(group_id: UUID, payload: PaymentCreate, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    item = GroupService(session).record_payment(current_user.user_id, current_user.user_id, group_id, payload)
    return success_response(data=PaymentRead.model_validate(item).model_dump(mode="json"), request=request)
