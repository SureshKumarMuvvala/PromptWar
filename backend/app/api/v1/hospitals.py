"""
Hospital lookup API route.
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import rate_limiter, verify_api_key
from app.models.schemas import HospitalSearchResponse
from app.services.google_maps import GoogleMapsService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])

# ── Service instance ─────────────────────────────────────────────────────────
_maps_service = GoogleMapsService()


@router.get("", response_model=HospitalSearchResponse, dependencies=[Depends(rate_limiter)])
async def get_nearby_hospitals(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(5.0, description="Search radius in km"),
    _: str = Depends(verify_api_key)
):
    """
    Search for nearby hospitals using Google Places API.
    """
    logger.info(f"Searching for hospitals near {lat}, {lng} (radius: {radius_km}km)")
    
    hospitals = await _maps_service.search_nearby_hospitals(
        lat=lat, 
        lng=lng, 
        radius_meters=int(radius_km * 1000)
    )

    return HospitalSearchResponse(hospitals=hospitals)
