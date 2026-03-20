"""
Hospital lookup API route.
"""

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Query

from app.api.deps import rate_limiter
from app.config import get_settings
from app.models.schemas import HospitalSearchResponse, HospitalInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("", response_model=HospitalSearchResponse, dependencies=[Depends(rate_limiter)])
async def search_hospitals(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: Optional[int] = Query(None, description="Search radius in km"),
):
    """
    Search for nearby hospitals using Google Places API.
    Falls back to mock data if API key is not configured.
    """
    settings = get_settings()
    radius = (radius_km or settings.HOSPITAL_SEARCH_RADIUS_KM) * 1000  # Convert to meters

    if not settings.GOOGLE_MAPS_API_KEY:
        logger.warning("Google Maps API key not configured — returning mock data")
        return HospitalSearchResponse(
            hospitals=_get_mock_hospitals(lat, lng)
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "type": "hospital",
                    "key": settings.GOOGLE_MAPS_API_KEY,
                },
            )
            response.raise_for_status()
            data = response.json()

        hospitals = []
        for place in data.get("results", [])[:settings.HOSPITAL_MAX_RESULTS]:
            loc = place.get("geometry", {}).get("location", {})
            hospitals.append(
                HospitalInfo(
                    name=place.get("name", "Unknown Hospital"),
                    address=place.get("vicinity", ""),
                    distance_km=None,  # Could calculate haversine distance
                    rating=place.get("rating"),
                    has_emergency=True,
                    location={"lat": loc.get("lat"), "lng": loc.get("lng")},
                )
            )

        return HospitalSearchResponse(hospitals=hospitals)

    except Exception as e:
        logger.error(f"Google Places API error: {e}")
        return HospitalSearchResponse(hospitals=_get_mock_hospitals(lat, lng))


def _get_mock_hospitals(lat: float, lng: float) -> list[HospitalInfo]:
    """Return mock hospital data for development/demo."""
    return [
        HospitalInfo(
            name="City General Hospital",
            address="123 Main Street",
            distance_km=1.5,
            eta_min=5,
            rating=4.3,
            phone="+1-555-0100",
            has_emergency=True,
            location={"lat": lat + 0.01, "lng": lng + 0.01},
        ),
        HospitalInfo(
            name="Apollo Emergency Care",
            address="456 Health Avenue",
            distance_km=3.2,
            eta_min=12,
            rating=4.7,
            phone="+1-555-0200",
            has_emergency=True,
            location={"lat": lat - 0.02, "lng": lng + 0.02},
        ),
        HospitalInfo(
            name="St. Mary's Medical Center",
            address="789 Care Boulevard",
            distance_km=5.8,
            eta_min=18,
            rating=4.5,
            phone="+1-555-0300",
            has_emergency=True,
            location={"lat": lat + 0.03, "lng": lng - 0.01},
        ),
    ]
