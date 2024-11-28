from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Index, Column
from sqlalchemy.dialects.postgresql import JSONB

class TraceLog(SQLModel, table=True):
    __tablename__ = "trace_logs"
    
    id: int = Field(primary_key=True)
    ts: str = Field(index=True)
    env: str = Field(index=True)
    server_ip: str = Field(index=True)
    client_addr: str = Field(index=True)
    method: str = Field(index=True)
    conversation_id: str = Field(index=True)
    message_id: str = Field(index=True)
    req_timestamp: Optional[str] = Field(index=True)
    
    trace_tree: dict = Field(sa_column=Column(JSONB))
    
    __table_args__ = (
        Index("idx_trace_env_ts", "env", "ts"),
        Index("idx_trace_conv_msg", "conversation_id", "message_id"),
        Index("idx_trace_method_ts", "method", "ts"),
    )
    
