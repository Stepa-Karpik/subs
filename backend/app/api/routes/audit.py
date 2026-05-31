from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.responses import success_response
from app.models.entities import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("")
def list_audit(request: Request, limit: int = Query(default=100, ge=1, le=500), current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    items = session.scalars(select(AuditLog).where(AuditLog.owner_subject_id == current_user.user_id).order_by(AuditLog.created_at.desc()).limit(limit)).all()
    return success_response(data=[{"id": str(item.id), "action": item.action, "target_type": item.target_type, "target_id": item.target_id, "payload": item.payload_json, "created_at": item.created_at.isoformat()} for item in items], request=request)
