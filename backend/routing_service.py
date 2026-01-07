import httpx
from logger import logger, error as log_error

class RoutingService:
    @staticmethod
    async def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float):
        """
        Get route from OSRM (Open Source Routing Machine)
        Returns polyline coordinates and duration/distance
        """
        try:
            url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                data = response.json()
            
            if data.get('code') != 'Ok':
                raise Exception('Routing failed')
            
            route = data['routes'][0]
            coordinates = [
                {
                    'latitude': coord[1],
                    'longitude': coord[0]
                }
                for coord in route['geometry']['coordinates']
            ]
            
            return {
                'success': True,
                'coordinates': coordinates,
                'distance': route['distance'],
                'duration': route['duration']
            }
        except Exception as error:
            log_error(f'Routing error: {str(error)}')
            return {
                'success': False,
                'error': str(error)
            }
