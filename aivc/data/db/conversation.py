from typing import List
from sqlmodel import Session, select
from aivc.common.chat import Conversation
from datetime import datetime
from aivc.config.config import L

def save_conversation(
    *,
    session: Session,
    conversation_id: str,
    role: str,
    content: str,
    question_type: str = None
) -> bool:
    try:
        conversation = Conversation(
            ts=datetime.now(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            question_type=question_type
        )
        session.add(conversation)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        L.error(f"save_conversation error: {str(e)}")
        return False


def get_conversation_history(
    *,
    session: Session,
    conversation_id: str
) -> List[Conversation]:
    stmt = select(Conversation).where(
        Conversation.conversation_id == conversation_id
    ).order_by(Conversation.id)
    
    conversations = session.exec(stmt).all()
    return conversations