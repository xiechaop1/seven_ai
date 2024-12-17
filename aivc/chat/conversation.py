from aivc.data.db import conversation
from typing import List, Dict, Any
from aivc.data.db.pg_engine import engine
from sqlmodel import Session
from aivc.common.task_class import QuestionType

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

def get_last_take_photo_question(conversation_id: str) -> str:
    with Session(engine) as session:
        conversation_list = conversation.get_conversation_history(
            session=session, 
            conversation_id=conversation_id)
        for conv in reversed(conversation_list):
            if conv.role == "user" and conv.question_type == QuestionType.TAKE_PHOTO.value:
                return conv.content

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