from __future__ import annotations

from datetime import datetime
from uuid import UUID
from app.schemas.common import BaseReadModel


class RecommendationRead(BaseReadModel):
    id: UUID
    target_type: str
    target_id: UUID
    type: str
    severity: str
    confidence: float
    title: str
    explanation: str
    estimated_saving_minor: int | None
    status: str
    created_at: datetime
    updated_at: datetime
