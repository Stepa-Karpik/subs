from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.responses import success_response
from app.schemas.forecast import ForecastMonthly, ForecastSummary, ScenarioRequest, ScenarioResponse
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecast", tags=["Forecast"])

@router.get("/summary")
def summary(request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    data = ForecastService(session).summary(current_user.user_id)
    return success_response(data=ForecastSummary.model_validate(data).model_dump(mode="json"), request=request)

@router.get("/monthly")
def monthly(request: Request, months: int = Query(default=12, ge=1, le=24), current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    data = {"months": ForecastService(session).monthly(current_user.user_id, months=months)}
    return success_response(data=ForecastMonthly.model_validate(data).model_dump(mode="json"), request=request)

@router.post("/scenario")
def scenario(payload: ScenarioRequest, request: Request, current_user=Depends(get_current_user), session: Session = Depends(get_db)):
    data = ForecastService(session).scenario(current_user.user_id, payload.subscription_ids, payload.group_ids)
    return success_response(data=ScenarioResponse.model_validate(data).model_dump(mode="json"), request=request)
