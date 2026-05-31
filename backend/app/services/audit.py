from __future__ import annotations

from sqlalchemy.orm import Session
from app.models.entities import AuditLog


def write_audit(session: Session, *, owner_subject_id: str, actor_subject_id: str, action: str, target_type: str, target_id: str, payload: dict | None = None) -> None:
    session.add(AuditLog(
        owner_subject_id=owner_subject_id,
        actor_subject_id=actor_subject_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        payload_json=payload or {},
    ))
