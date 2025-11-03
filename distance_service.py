"""
Distance calculation service with Google Maps Distance Matrix API
Falls back to Haversine formula if Google Maps is not available
"""
import os
import math
from typing import Optional, List, Dict
import googlemaps
from datetime import datetime


def calculate_haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Haversine formula for straight-line distance calculation
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return round(distance, 2)  # Round to 2 decimal places


class DistanceService:
    """Service for calculating distances using Google Maps or Haversine"""

    def __init__(self, google_maps_api_key: Optional[str] = None):
        self.api_key = google_maps_api_key
        self.gmaps_client = None

        if google_maps_api_key:
            try:
                self.gmaps_client = googlemaps.Client(key=google_maps_api_key)
                print("Google Maps Distance Matrix API enabled")
            except Exception as e:
                print(f"Google Maps client initialization failed: {e}")
                print("Using Haversine distance (straight-line)")
        else:
            print("Google Maps API key not provided - using Haversine distance (straight-line)")

    def calculate_distance(
        self, from_lat: float, from_lon: float, to_lat: float, to_lon: float
    ) -> Dict:
        """
        Calculate distance between two GPS coordinates
        Uses Google Maps if available, falls back to Haversine
        """
        # Try Google Maps first if available
        if self.gmaps_client and self.api_key:
            try:
                result = self._get_google_maps_distance(from_lat, from_lon, to_lat, to_lon)
                if result:
                    return result
            except Exception as error:
                print(f"Google Maps API error, falling back to Haversine: {error}")

        # Fallback to Haversine (straight-line distance)
        distance_km = calculate_haversine_distance(from_lat, from_lon, to_lat, to_lon)
        return {
            "distance_km": distance_km,
            "distance_text": f"{distance_km} km",
            "method": "haversine",
        }

    def _get_google_maps_distance(
        self, from_lat: float, from_lon: float, to_lat: float, to_lon: float
    ) -> Optional[Dict]:
        """
        Get road distance from Google Maps Distance Matrix API
        """
        if not self.gmaps_client or not self.api_key:
            return None

        try:
            print("Calling Google Maps Distance Matrix API...")
            print(f"   Origin: {from_lat},{from_lon}")
            print(f"   Destination: {to_lat},{to_lon}")
            print(f"   Timestamp: {datetime.now().isoformat()}")

            result = self.gmaps_client.distance_matrix(
                origins=[(from_lat, from_lon)],
                destinations=[(to_lat, to_lon)],
                mode="driving",
                departure_time=datetime.now(),  # Request real-time traffic data
            )

            print("Google Maps API Response received")

            # Check if request was successful
            if result["status"] != "OK":
                print(f"Google Maps API error: {result['status']}")
                return None

            element = result["rows"][0]["elements"][0]
            if element["status"] != "OK":
                print("Google Maps route not found")
                return None

            # Extract distance and duration
            distance_meters = element["distance"]["value"]
            distance_km = round(distance_meters / 1000, 2)
            duration_seconds = element["duration"]["value"]
            duration_minutes = round(duration_seconds / 60)

            # Check if duration_in_traffic is available (real-time traffic)
            traffic_duration_seconds = element.get("duration_in_traffic", {}).get("value")
            traffic_duration_minutes = (
                round(traffic_duration_seconds / 60) if traffic_duration_seconds else None
            )

            print(f"   Distance: {distance_km} km ({element['distance']['text']})")
            print(f"   Duration (no traffic): {duration_minutes} mins ({element['duration']['text']})")
            if traffic_duration_minutes:
                print(
                    f"   Duration (with traffic): {traffic_duration_minutes} mins "
                    f"({element.get('duration_in_traffic', {}).get('text', '')})"
                )

            return {
                "distance_km": distance_km,
                "distance_text": element["distance"]["text"],
                "duration_minutes": traffic_duration_minutes or duration_minutes,
                "duration_text": (
                    element.get("duration_in_traffic", {}).get("text")
                    or element["duration"]["text"]
                ),
                "method": "google_maps",
            }
        except Exception as error:
            print(f"Error calling Google Maps API: {error}")
            return None

    def calculate_multiple_distances(
        self, from_lat: float, from_lon: float, destinations: List[Dict[str, float]]
    ) -> List[Dict]:
        """
        Calculate multiple distances at once (batch request)
        More efficient than calling calculate_distance multiple times
        """
        # Try Google Maps batch request if available
        if self.gmaps_client and self.api_key and len(destinations) > 1:
            try:
                result = self._get_batch_google_maps_distances(from_lat, from_lon, destinations)
                if result:
                    return result
            except Exception as error:
                print(f"Google Maps batch API error, falling back to Haversine: {error}")

        # Fallback to Haversine for each destination
        results = []
        for dest in destinations:
            distance_km = calculate_haversine_distance(
                from_lat, from_lon, dest["lat"], dest["lon"]
            )
            results.append({
                "distance_km": distance_km,
                "distance_text": f"{distance_km} km",
                "method": "haversine",
            })
        return results

    def _get_batch_google_maps_distances(
        self, from_lat: float, from_lon: float, destinations: List[Dict[str, float]]
    ) -> Optional[List[Dict]]:
        """
        Get batch distances from Google Maps (more efficient)
        """
        if not self.gmaps_client or not self.api_key:
            return None

        try:
            destination_coords = [(dest["lat"], dest["lon"]) for dest in destinations]

            print("Calling Google Maps Distance Matrix API (BATCH)...")
            print(f"   Origin: {from_lat},{from_lon}")
            print(f"   Destinations: {len(destinations)} locations")
            print(f"   Timestamp: {datetime.now().isoformat()}")

            result = self.gmaps_client.distance_matrix(
                origins=[(from_lat, from_lon)],
                destinations=destination_coords,
                mode="driving",
                departure_time=datetime.now(),  # Request real-time traffic data
            )

            print("Google Maps API Batch Response received")

            if result["status"] != "OK":
                print(f"Google Maps batch API error: {result['status']}")
                return None

            elements = result["rows"][0]["elements"]
            results = []

            for idx, element in enumerate(elements):
                if element["status"] != "OK":
                    # Fallback to Haversine for this destination
                    dest = destinations[idx]
                    distance_km = calculate_haversine_distance(
                        from_lat, from_lon, dest["lat"], dest["lon"]
                    )
                    print(f"   Destination {idx + 1}: Fallback to Haversine ({distance_km} km)")
                    results.append({
                        "distance_km": distance_km,
                        "distance_text": f"{distance_km} km",
                        "method": "haversine",
                    })
                    continue

                distance_meters = element["distance"]["value"]
                distance_km = round(distance_meters / 1000, 2)
                duration_seconds = element["duration"]["value"]
                duration_minutes = round(duration_seconds / 60)

                # Check if duration_in_traffic is available (real-time traffic)
                traffic_duration_seconds = element.get("duration_in_traffic", {}).get("value")
                traffic_duration_minutes = (
                    round(traffic_duration_seconds / 60) if traffic_duration_seconds else None
                )

                traffic_suffix = " (with traffic)" if traffic_duration_minutes else ""
                print(
                    f"   Destination {idx + 1}: {distance_km} km, "
                    f"{traffic_duration_minutes or duration_minutes} mins{traffic_suffix}"
                )

                results.append({
                    "distance_km": distance_km,
                    "distance_text": element["distance"]["text"],
                    "duration_minutes": traffic_duration_minutes or duration_minutes,
                    "duration_text": (
                        element.get("duration_in_traffic", {}).get("text")
                        or element["duration"]["text"]
                    ),
                    "method": "google_maps",
                })

            return results
        except Exception as error:
            print(f"Error calling Google Maps batch API: {error}")
            return None

    def is_google_maps_available(self) -> bool:
        """Check if Google Maps is available"""
        return self.gmaps_client is not None and self.api_key is not None


# Singleton instance
_distance_service_instance: Optional[DistanceService] = None


def initialize_distance_service(google_maps_api_key: Optional[str] = None) -> DistanceService:
    """Initialize the distance service singleton"""
    global _distance_service_instance
    if _distance_service_instance is None:
        _distance_service_instance = DistanceService(google_maps_api_key)
    return _distance_service_instance


def get_distance_service() -> DistanceService:
    """Get the distance service singleton"""
    global _distance_service_instance
    if _distance_service_instance is None:
        raise RuntimeError("Distance service not initialized. Call initialize_distance_service() first.")
    return _distance_service_instance
