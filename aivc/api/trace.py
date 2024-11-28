from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select, and_
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
from aivc.data.db.trace_log import TraceLog
from aivc.data.db.pg_engine import engine
from enum import Enum
from zoneinfo import ZoneInfo

router = APIRouter()

class TimeRange(str, Enum):
    TODAY = "today"
    LAST_3_DAYS = "last_3_days" 
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    CUSTOM = "custom"

class TraceLogResponse(BaseModel):
    id: int
    ts: str
    env: str
    server_ip: str
    client_addr: str
    method: str
    conversation_id: str
    message_id: str
    trace_tree: dict

class TraceLogListResponse(BaseModel):
    total: int
    items: List[TraceLogResponse]

class TraceLogRequest(BaseModel):
    # API密钥
    key: str
    
    # 分页参数
    page: int = 1
    page_size: int = 20
    
    # 时间范围参数
    time_range: TimeRange = TimeRange.TODAY
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    # 过滤条件
    env: Optional[str] = None
    server_ip: Optional[str] = None
    client_addr: Optional[str] = None
    method: Optional[str] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None

def get_time_with_timezone(dt: datetime) -> str:
    return dt.astimezone(ZoneInfo("Asia/Shanghai")).isoformat()

def convert_to_trace_log_response(trace_log: TraceLog) -> TraceLogResponse:
    return TraceLogResponse(
        id=trace_log.id,
        ts=trace_log.ts,
        env=trace_log.env,
        server_ip=trace_log.server_ip,
        client_addr=trace_log.client_addr,
        method=trace_log.method,
        conversation_id=trace_log.conversation_id,
        message_id=trace_log.message_id,
        trace_tree=trace_log.trace_tree or {}  
    )

@router.post("/", response_model=TraceLogListResponse)
async def get_traces(request: TraceLogRequest):
    """
    获取追踪日志列表，支持时间范围和多种过滤条件
    """

    API_KEY = "gQewyXpQRTG"  
    if request.key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # 验证分页参数
    if request.page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page number must be greater than 0"
        )
    if not 1 <= request.page_size <= 100:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 100"
        )
    
    query = select(TraceLog)
    filters = []
    
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    if request.time_range == TimeRange.CUSTOM:
        if not (request.start_time and request.end_time):
            raise HTTPException(
                status_code=400,
                detail="Custom time range requires both start_time and end_time"
            )
        start_time = request.start_time
        end_time = request.end_time
    else:
        if request.time_range == TimeRange.TODAY:
            start_time = get_time_with_timezone(
                now.replace(hour=0, minute=0, second=0, microsecond=0)
            )
            end_time = get_time_with_timezone(now)
        elif request.time_range == TimeRange.LAST_3_DAYS:
            start_time = get_time_with_timezone(
                (now - timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0)
            )
            end_time = get_time_with_timezone(now)
        elif request.time_range == TimeRange.LAST_WEEK:
            start_time = get_time_with_timezone(
                (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
            )
            end_time = get_time_with_timezone(now)
        elif request.time_range == TimeRange.LAST_MONTH:
            start_time = get_time_with_timezone(
                (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
            )
            end_time = get_time_with_timezone(now)
    
    filters.append(TraceLog.ts.between(start_time, end_time))
    
    # 添加其他过滤条件
    if request.env:
        filters.append(TraceLog.env == request.env)
    if request.server_ip:
        filters.append(TraceLog.server_ip == request.server_ip)
    if request.client_addr:
        filters.append(TraceLog.client_addr == request.client_addr)
    if request.method:
        filters.append(TraceLog.method == request.method)
    if request.conversation_id:
        filters.append(TraceLog.conversation_id == request.conversation_id)
    if request.message_id:
        filters.append(TraceLog.message_id == request.message_id)
    
    # 应用过滤条件
    query = query.where(and_(*filters))
    
    # 按时间倒序排序
    query = query.order_by(TraceLog.ts.desc())
    
    with Session(engine) as session:
        # 计算总数
        total = len(session.exec(query).all())
        
        # 分页
        query = query.offset((request.page - 1) * request.page_size).limit(request.page_size)
        items = session.exec(query).all()
        
        # 转换结果
        response_items = [convert_to_trace_log_response(item) for item in items]
    
    return TraceLogListResponse(total=total, items=response_items)