from fastapi import APIRouter

from app.routers import auth, cards, dev, evolution, health, insights, jots, promises, signals

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dev.router)
api_router.include_router(cards.router)
api_router.include_router(signals.router)
api_router.include_router(promises.router)
api_router.include_router(insights.router)
api_router.include_router(jots.router)
api_router.include_router(evolution.router)
