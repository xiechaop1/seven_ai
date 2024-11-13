from typing import List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Index, text
from pgvector.sqlalchemy import Vector
from dataclasses import dataclass

class QuestionCategory(SQLModel, table=True):
    __tablename__ = "question_categories"
    
    id: int = Field(primary_key=True)
    category_name: str = Field(index=True, unique=True)
    answer: str
    
    questions: List["Question"] = Relationship(back_populates="category")
    
    __table_args__ = (
        Index("idx_category_name", "category_name"),
    )

class Question(SQLModel, table=True):
    __tablename__ = "questions"
    
    id: int = Field(default=None, primary_key=True)
    question: str = Field(nullable=False, unique=True, index=True)
    vector: List[float] = Field(sa_column=Column(Vector(1792)))
    
    category_id: int = Field(foreign_key="question_categories.id")
    category: QuestionCategory = Relationship(back_populates="questions")
    
    __table_args__ = (
        Index("idx_question", "question"),
        Index(
            "idx_question_vector_hnsw",
            text("vector vector_ip_ops"), 
            postgresql_using="hnsw",
            postgresql_with={
                "m": 16,
                "ef_construction": 64
            },
        ),
    )

@dataclass
class KBSearchResult:
    id: int
    question: str
    category_name: str 
    answer: str
    similarity: float