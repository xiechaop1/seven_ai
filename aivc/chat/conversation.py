from aivc.data.db import conversation
from typing import List, Dict, Any
from aivc.data.db.pg_engine import engine
from sqlmodel import Session

def get_conversation_history(conversation_id: str) -> List[Dict[str, Any]]:
    messages = []
    with Session(engine) as session:
        conversation_list = conversation.get_conversation_history(
            session=session, 
            conversation_id=conversation_id)
        for conv in conversation_list:
            messages.append({
                "role": conv.role,
                "content": conv.content
            })
    return messages


def save_conversation(conversation_id: str, 
                    question: str, 
                    answer: str,
                    question_type:str = None) -> bool:
    with Session(engine) as session:
        conversation.save_conversation(
            session=session,
            conversation_id=conversation_id,
            role="user",
            content=question,
            question_type=question_type
        )

        conversation.save_conversation(
            session=session,
            conversation_id=conversation_id,
            role="assistant",
            content=answer
        )