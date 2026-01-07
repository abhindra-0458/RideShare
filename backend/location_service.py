import math

class LocationService:
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two coordinates using Haversine formula (km)
        """
        R = 6371  # Earth's radius in kilometers
        
        d_lat = (lat2 - lat1) * (math.pi / 180)
        d_lon = (lon2 - lon1) * (math.pi / 180)
        
        a = (math.sin(d_lat / 2) * math.sin(d_lat / 2) +
             math.cos(lat1 * (math.pi / 180)) * math.cos(lat2 * (math.pi / 180)) *
             math.sin(d_lon / 2) * math.sin(d_lon / 2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def validate_location(latitude: float, longitude: float) -> bool:
        """Validate latitude and longitude ranges"""
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False
        if latitude < -90 or latitude > 90:
            return False
        if longitude < -180 or longitude > 180:
            return False
        return True
