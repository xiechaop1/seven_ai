from pydantic import BaseModel 
 
class QueryAnalyzer(BaseModel):
    question: str

     