from typing import List
from enum import Enum

class QuestionType(Enum):
    DEFAULT = 'default'
    ABOUT = 'about'
    SUPPORT = 'support'
    SONG = 'song'
    TAKE_PHOTO = 'take_photo'
    PHOTO_RECOGNITION = 'photo_recognition'
    WEATHER = 'weather'

QuestionWithAnswer = [QuestionType.ABOUT.value, QuestionType.SUPPORT.value]

class TaskClass:
    def __init__(self, 
            name: str, 
            similar_words: List[str]=[],
            keywords: list=[],
            vector: List[float]=[]):
        self.name = name
        self.similar_words = similar_words
        self.keywords = keywords
        self.vector = vector

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"], 
            similar_words=data["similar_words"],
            keywords=data["keywords"],
            vector=data.get("vector", []))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "similar_words": self.similar_words,
            "keywords": self.keywords,
            "vector": self.vector
        }

