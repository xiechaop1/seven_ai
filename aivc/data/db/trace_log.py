from aivc.common.trace_tree import TraceTree
from aivc.common.trace_log import TraceLog
from sqlmodel import Session, select
from typing import Optional, List
import json
from aivc.config.config import L

def save_trace(session: Session, trace_tree: TraceTree):
    try:
        log_entry = TraceLog(
            ts=trace_tree.root.ts,
            env=trace_tree.root.env,
            server_ip=trace_tree.root.server_ip,
            client_addr=trace_tree.root.client_addr,
            method=trace_tree.root.method,
            conversation_id=trace_tree.root.conversation_id,
            message_id=trace_tree.root.message_id,
            req_timestamp=trace_tree.root.req_timestamp,
            trace_tree=json.loads(str(trace_tree))
        )
        session.add(log_entry)
        session.commit()
        return log_entry
    except Exception as e:
        L.error(f"save_trace error: {str(e)}")
        session.rollback()
        raise e

def get_trace_by_message_id(session: Session, message_id: str) -> Optional[TraceLog]:
    statement = select(TraceLog).where(TraceLog.message_id == message_id)
    result = session.exec(statement).first()
    return result

def get_traces(session: Session, limit: int = 300) -> List[TraceLog]:
    statement = select(TraceLog).order_by(TraceLog.ts.desc()).limit(limit)
    results = session.exec(statement).all()
    return results

def get_traces_by_conversation_id(session: Session, conversation_id: str) -> List[TraceLog]:
    statement = select(TraceLog).where(
        TraceLog.conversation_id == conversation_id
    ).order_by(TraceLog.ts.asc())
    return session.exec(statement).all()

def get_traces_by_time_range(
    session: Session,
    start_time: str,
    end_time: str,
    limit: int = 1000
) -> List[TraceLog]:
    statement = select(TraceLog).where(
        TraceLog.ts.between(start_time, end_time)
    ).order_by(TraceLog.ts.desc()).limit(limit)
    return session.exec(statement).all()

def get_traces_by_env(
    session: Session,
    env: str,
    limit: int = 300
) -> List[TraceLog]:
    statement = select(TraceLog).where(
        TraceLog.env == env
    ).order_by(TraceLog.ts.desc()).limit(limit)
    return session.exec(statement).all()