"""
Google Maps / Places API service for hospital lookups and geolocation.
"""

import httpx
from typing import Optional, List
from app.config import get_settings
from app.models.schemas import HospitalInfo
from app.utils.logger import get_logger

logger = get_logger(__name__)

class GoogleMapsService:
    """Interface for Google Maps and Places APIs."""

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"

    async def search_nearby_hospitals(
        self, 
        lat: float, 
        lng: float, 
        radius_meters: int = 5000
    ) -> List[HospitalInfo]:
        """
        Search for nearby hospitals using Google Places API (Nearby Search).
        """
        if not self.api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not configured, returning empty list")
            return []

        url = f"{self.base_url}/place/nearbysearch/json"
        params = {
            "location": f"{lat},{lng}",
            "radius": radius_meters,
            "type": "hospital",
            "key": self.api_key
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "OK" and data.get("status") != "ZERO_RESULTS":
                    logger.error(f"Google Places API error: {data.get('status')} - {data.get('error_message')}")
                    return []

                hospitals = []
                for result in data.get("results", []):
                    geometry = result.get("geometry", {})
                    location = geometry.get("location", {})
                    
                    hospitals.append(HospitalInfo(
                        name=result.get("name", "Unknown Hospital"),
                        address=result.get("vicinity"),
                        distance_km=None,
                        rating=result.get("rating"),
                        location={
                            "lat": location.get("lat"),
                            "lng": location.get("lng")
                        } if location else None,
                        has_emergency=True
                    ))
                
                return hospitals[:5]  # Return top 5
            except Exception as e:
                logger.error(f"Failed to fetch hospitals from Google Maps: {e}")
                return []
