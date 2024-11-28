from typing import Optional
from pydantic import BaseModel

class IPLocation(BaseModel):
    status: Optional[str] = None
    country: Optional[str] = None
    countryCode: Optional[str] = None
    region: Optional[str] = None
    regionName: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    query: Optional[str] = None
    message: Optional[str] = None

DEFAULT_SHANGHAI_LOCATION = IPLocation(
    status='success',
    country='China',
    countryCode='CN',
    region='SH',
    regionName='Shanghai',
    city='Shanghai',
    lat=31.2222,
    lon=121.4581,
    query='local',
    message=None
)