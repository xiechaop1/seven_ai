from typing import List
from sqlmodel import Session, select
from sqlalchemy import text
from aivc.common.kb import QuestionCategory, Question, KBSearchResult

def create_category(
    *,
    session: Session,
    category_name: str,
    answer: str
) -> QuestionCategory:
    stmt = select(QuestionCategory).where(QuestionCategory.category_name == category_name)
    existing_category = session.exec(stmt).first()
    
    if existing_category:
        existing_category.answer = answer
        session.add(existing_category)
        session.commit()
        session.refresh(existing_category)
        return existing_category
    
    category = QuestionCategory(category_name=category_name, answer=answer)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

def create_question(
    *,
    session: Session,
    question: str,
    vector: List[float],
    category_id: int
) -> Question:
    stmt = select(Question).where(Question.question == question)
    existing_question = session.exec(stmt).first()
    
    if existing_question:
        existing_question.vector = vector
        existing_question.category_id = category_id
        session.add(existing_question)
        session.commit()
        session.refresh(existing_question)
        return existing_question
    
    question_obj = Question(
        question=question,
        vector=vector,
        category_id=category_id
    )
    session.add(question_obj)
    session.commit()
    session.refresh(question_obj)
    return question_obj
    
def search_similar_questions(
    *,
    session: Session,
    vector: List[float], 
    top_k: int = 5,
    threshold: float = -0.83
) -> List[KBSearchResult]:
    session.exec(text("SET LOCAL enable_seqscan = OFF"))
    session.exec(text("SET LOCAL hnsw.ef_search = 20")) 
    session.exec(text("SET LOCAL enable_bitmapscan = OFF"))
    session.exec(text("SET LOCAL enable_tidscan = OFF"))

    statement = text("""
        WITH vector_search AS (
            SELECT 
                q.id,
                q.question,
                qc.category_name,
                qc.answer,
                q.vector <#> cast(:search_vector as vector) as distance
            FROM questions q
            JOIN question_categories qc ON q.category_id = qc.id
            ORDER BY q.vector <#> cast(:search_vector as vector)
            LIMIT :top_k
        )
        SELECT 
            id,
            question,
            category_name,
            answer,
            distance
        FROM vector_search
        WHERE distance <= :threshold
        ORDER BY distance;
    """)
    
    params = {
        "search_vector": vector,
        "top_k": top_k,
        "threshold": threshold
    }
    
    results = session.exec(statement=statement, params=params).all()
    
    search_results = [
        KBSearchResult(
            id=result[0],
            question=result[1], 
            category_name=result[2],
            answer=result[3],
            similarity=result[4]
        )
        for result in results
    ]
    
    return search_results