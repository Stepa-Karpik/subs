from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.models.entities import PaymentRecord, RegionalCostBaseline


@dataclass(frozen=True)
class EstimateResult:
    amount_minor: int | None
    strategy: str
    confidence: str


class VariableEstimateService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def estimate(self, *, owner_subject_id: str, source_type: str, source_id: UUID, category_key: str | None = None, country: str | None = None, city: str | None = None) -> EstimateResult:
        payments = self.session.scalars(
            select(PaymentRecord)
            .where(
                PaymentRecord.owner_subject_id == owner_subject_id,
                PaymentRecord.source_type == source_type,
                PaymentRecord.source_id == source_id,
            )
            .order_by(desc(PaymentRecord.paid_at))
            .limit(6)
        ).all()
        if payments:
            amount = round(sum(item.amount_minor for item in payments) / len(payments))
            confidence = "high" if len(payments) >= 4 else "medium"
            return EstimateResult(amount, "user_history_avg", confidence)
        if category_key and country:
            stmt = select(RegionalCostBaseline).where(
                RegionalCostBaseline.country_code == country,
                RegionalCostBaseline.category_key == category_key,
            )
            if city:
                city_item = self.session.scalar(stmt.where(RegionalCostBaseline.city == city))
                if city_item:
                    return EstimateResult(city_item.amount_minor, "city_baseline", city_item.confidence)
            country_item = self.session.scalar(stmt.where(RegionalCostBaseline.city.is_(None)))
            if country_item:
                return EstimateResult(country_item.amount_minor, "country_baseline", country_item.confidence)
        return EstimateResult(None, "none", "low")
