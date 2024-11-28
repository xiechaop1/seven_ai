from pydantic import BaseModel, Field
from aivc.common.query_analyze import QueryAnalyzer
from aivc.common.kb import KBSearchResult
from aivc.common.chat import Prompt

class Route(BaseModel):
    query_analyzer: QueryAnalyzer = Field(default_factory=QueryAnalyzer)
    kb_result: KBSearchResult = Field(default=None)
    prompt: Prompt =  Field(default_factory=Prompt)