from aivc.config.config import settings
from aivc.utils.ip import IP
from aivc.utils.tools import get_time_str
from pydantic import BaseModel, Field
import json
from typing import Optional

class TraceRoot(BaseModel):
    ts: str = Field(default_factory=get_time_str)

    env: str = settings.ENV
    server_ip: str = IP
    client_addr: str = ""

    method: str = ""
    conversation_id: str = ""
    message_id: str = ""
    req_timestamp: Optional[str] = ""

    srt_cost: int = 0
    llm_first_cost: int = 0
    tts_first_cost: int = 0

    total_price: float = 0.0

    err_code: int = 0
    err_message: str = ""

class TraceQPP(BaseModel):
    question_category: str = ""
    max_score: float = 0.0
    cost: int = 0

class TraceSRT(BaseModel):
    cost: int = 0
    code: int = 0
    message: str = ""
    text: str = ""
 
class TraceLLM(BaseModel):
    provider: str = ""
    model: str = ""
    answer: str = ""
    req_tokens: int = 0
    resp_tokens: int = 0
    first_cost: int = 0
    cost: int = 0
    price: float = 0.0


class TraceTTSResp(BaseModel):
    text: Optional[str] = ""
    audio_file: Optional[str] = ""
    audio_file_size: Optional[int] = 0
    cost: Optional[int] = 0
    stream_seq: Optional[int] = 0

class TraceTTS(BaseModel):
    first_cost: int = 0
    cost: int = 0
    resp_list: list[TraceTTSResp] = []
    price: float = 0.0
    
class TraceTree(BaseModel):
    root: TraceRoot = Field(default_factory=TraceRoot)
    qpp: TraceQPP = Field(default_factory=TraceQPP)
    srt: TraceSRT = Field(default_factory=TraceSRT) 
    llm: TraceLLM = Field(default_factory=TraceLLM) 
    tts: TraceTTS = Field(default_factory=TraceTTS) 

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False, indent=2)
