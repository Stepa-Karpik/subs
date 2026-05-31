from fastapi import APIRouter, Depends, Request
from app.api.deps import get_current_user
from app.core.responses import success_response

router = APIRouter(prefix="/me", tags=["Me"])

@router.get("")
def me(request: Request, current_user=Depends(get_current_user)):
    return success_response(data=current_user.model_dump(), request=request)
