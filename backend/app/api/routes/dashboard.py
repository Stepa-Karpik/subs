from datetime import date
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.responses import success_response
from app.schemas.common import DashboardSummary
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary")
def dashboard_summary(request: Request, month: str | None = Query(default=None), current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    parsed = None
    if month:
        year, mon = [int(part) for part in month.split("-", 1)]
        parsed = date(year, mon, 1)
    data = ForecastService(session).dashboard(current_user.user_id, month=parsed)
    return success_response(data=DashboardSummary.model_validate(data).model_dump(mode="json"), request=request)
