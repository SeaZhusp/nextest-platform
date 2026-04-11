from fastapi import APIRouter

from app.api.endpoints import auth, health

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
