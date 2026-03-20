"""
API v1 router — aggregates all versioned routes.
"""

from fastapi import APIRouter

from app.api.v1.emergency import router as emergency_router
from app.api.v1.hospitals import router as hospitals_router

router = APIRouter(prefix="/api/v1")
router.include_router(emergency_router)
router.include_router(hospitals_router)
