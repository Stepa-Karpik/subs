from fastapi import APIRouter
from app.api.routes import admin, audit, dashboard, forecast, groups, integrations, me, recommendations, subscriptions

api_router = APIRouter()
api_router.include_router(me.router)
api_router.include_router(dashboard.router)
api_router.include_router(subscriptions.router)
api_router.include_router(groups.router)
api_router.include_router(forecast.router)
api_router.include_router(recommendations.router)
api_router.include_router(integrations.router)
api_router.include_router(audit.router)
api_router.include_router(admin.router)
