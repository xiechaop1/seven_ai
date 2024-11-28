import aiohttp
from typing import Dict, Tuple
from datetime import datetime, timedelta
from aivc.utils import city_location
from aivc.common import ip
from aivc.utils.ip2region_local import ip_region
from aivc.config.config import L

class WeatherService:
    _instance = None
    _cache: Dict[str, Tuple[dict, datetime]] = {}
    API_KEY = "6ee84867e58c478093d7eb395e4b13b7"
    BASE_URL = "https://devapi.qweather.com/v7/weather/7d"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_cache_key(self, lon: float, lat: float) -> str:
        return f"{lon},{lat}"

    def _is_cache_expired(self, cache_time: datetime) -> bool:
        return datetime.now() - cache_time > timedelta(days=3)

    async def get_weather(self, lon: float, lat: float) -> dict:
        cache_key = self._get_cache_key(lon, lat)
        
        if cache_key in self._cache:
            data, cache_time = self._cache[cache_key]
            if not self._is_cache_expired(cache_time):
                return data
            
        params = {
            'location': f"{lon},{lat}",
            'key': self.API_KEY
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL, params=params) as response:
                result = await response.json()
                weather_data = result.get('daily', [])
                if response.status == 200:
                    self._cache[cache_key] = (weather_data, datetime.now())
                    return weather_data
                raise Exception(f"Weather API error: {response.status}")
    
    async def get_location(self, question: str, ip:str) -> ip.IPLocation:
        # TODO: get city from question by 大模型
        city = await city_location.get_city(question)
        L.info(f"get_location question: {question}, city: {city}")
        if city:
            location = await city_location.get_city_location(city)
            return location
        else:
            return await ip_region(ip)
        

if __name__ == "__main__":
    import asyncio
    async def main():
        result = await WeatherService().get_weather(116.4074, 39.9042)
        print(result)
        
    asyncio.run(main())
