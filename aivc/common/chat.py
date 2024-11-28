from pydantic import BaseModel
import tiktoken
from aivc.chat.llm.providers.openai_llm import OpenAILLM
from typing import Optional, TypeVar, Generic
from enum import Enum
from sqlmodel import SQLModel, Field
from sqlalchemy import Index
from datetime import datetime

class VCMethod(str, Enum):
    VOICE_CHAT = "voice-chat"
    TEXT_CHAT = "text-chat"
    PING = "ping"


class ContentType(str, Enum):
    AUDIO = "audio"
    IMAGE = "image"

class VCReqData(BaseModel):
    content_type: Optional[str] = ContentType.AUDIO.value  # audio or image
    content: Optional[str] = "" # base64 encoded data

DataT = TypeVar("DataT")

class Req(BaseModel, Generic[DataT]):
    version: str = "1.0"
    method: VCMethod 
    conversation_id: str
    message_id: str
    token: Optional[str] = ""
    timestamp: Optional[str] = ""
    data: Optional[DataT] = None

class VCRespData(BaseModel):
    action: Optional[str] = None
    text: Optional[str] = None
    audio_format: Optional[str] = "pcm"
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    sample_format: Optional[str] = None
    bitrate: Optional[int] = None
    audio_data: Optional[str] = None
    stream_seq: int = 0
    
class Resp(BaseModel, Generic[DataT]):
    version: Optional[str] = ""
    method: Optional[VCMethod] = ""
    conversation_id: Optional[str] = ""
    message_id: Optional[str] = ""
    code: int = 0
    message: str = "success"
    data: Optional[DataT] = None

    def __str__(self):
        data_str = ""
        if isinstance(self.data, VCRespData):
            data_str = f"audio_format:{self.data.audio_format} audio_data len: {len(self.data.audio_data)} text: {self.data.text} stream_seq: {self.data.stream_seq}"
        return f"version: {self.version} method: {self.method} conversation_id: {self.conversation_id} message_id: {self.message_id} code: {self.code} message: {self.message} data:: {data_str}"

class Prompt(BaseModel):
    system: Optional[str] = ""
    user: Optional[str] = ""

# Define the Chat
class Chat(BaseModel):
    id: str

# Define the Model
class Model(BaseModel):
    name: str

def num_tokens_from_string(string: str, model: str = OpenAILLM.GPT35_TURBO) -> int:
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def get_prompt_length(prompt: str, encoding_name: str = "cl100k_base") -> int:
    # if not str return 0
    if not isinstance(prompt, str):
        return 0
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(prompt))

def trim_prompt_to_length(
        prompt: str, 
        length: int, 
        encoding_name: str = "cl100k_base") -> str:
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(prompt)

    if len(tokens) > length:
        tokens = tokens[:length]
        trimmed_prompt = encoding.decode(tokens)
    else:
        trimmed_prompt = prompt
    return trimmed_prompt


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    
    id: int = Field(primary_key=True) 
    ts: datetime = Field(nullable=False)
    conversation_id: str = Field(nullable=False)
    role: str = Field(nullable=False)
    content: str = Field(nullable=False)
    question_type: str = Field(nullable=True)
    
    __table_args__ = (
        # 复合索引:对话ID+id
        Index("idx_conv_id", "conversation_id", "id"),\
    )

class HandlerResult:
    def __init__(self, question: str, answer: str, question_type: str):
        self.question = question
        self.answer = answer
        self.question_type = question_type