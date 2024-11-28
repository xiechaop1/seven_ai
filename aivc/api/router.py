from fastapi import APIRouter
from aivc.api import trace

api_router_v1 = APIRouter()
api_router_v1.include_router(trace.router,prefix="/trace",tags=["trace"])

