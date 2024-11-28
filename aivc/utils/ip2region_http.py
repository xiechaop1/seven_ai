from typing import Optional, Dict
import aiohttp
import asyncio
import time
from aivc.common import ip
from aivc.utils.ip import is_private_ip

class IPLocator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._cache: Dict[str, ip.IPLocation] = {}
            self._session: Optional[aiohttp.ClientSession] = None
            self._initialized = True
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            
    async def get_location(self, ip_address: str) -> Optional[ip.IPLocation]:
        if is_private_ip(ip_address):
            default_location = ip.DEFAULT_SHANGHAI_LOCATION
            default_location.query = ip_address
            return default_location
            
        if ip_address in self._cache:
            return self._cache[ip_address]
            
        fields = "status,message,country,countryCode,region,regionName,city,lat,lon,query"
        url = f"http://ip-api.com/json/{ip_address}?fields={fields}"
        
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        try:
            async with self._session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    location = ip.IPLocation(**data)
                    self._cache[ip_address] = location
                    return location
        except Exception as e:
            print(f"获取IP位置信息失败: {str(e)}")
            return None


async def main():
    start_time = time.time()
    async with IPLocator() as locator:
        location = await locator.get_location("223.166.190.236")
        print(location, time.time()-start_time)

if __name__ == "__main__":
    asyncio.run(main())