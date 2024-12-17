from aivc.chat.llm.base import BaseLLM
from enum import Enum
from typing import Dict, Any, Type
from aivc.config.config import settings,L
from aivc.chat.llm.providers.openai_llm import OpenAILLM
from aivc.chat.llm.providers.deepseek import DeepSeekLLM
from aivc.chat.llm.providers.wenxin import WenxinLLM
from aivc.chat.llm.providers.qwen import QWenLLM
from aivc.chat.llm.providers.zhipu import ZhiPuLLM
from aivc.chat.llm.providers.moonshot import MoonShotLLM
from aivc.chat.llm.providers.ollama import OllamaLLM
from aivc.chat.llm.providers.doubao import DouBaoLLM
from aivc.chat.llm.providers.siliconflow import SiliconFlowLLM
from aivc.chat.llm.providers.step import StepLLM
from aivc.chat.llm.providers.baichuan import BaiChuanLLM
from pydantic import BaseModel, field_validator
from transformers import AutoTokenizer
import tiktoken

class LLMType(Enum):
    OPENAI = OpenAILLM.PROVIDER
    DEEPSEEK = DeepSeekLLM.PROVIDER
    WENXIN = WenxinLLM.PROVIDER
    QWEN = QWenLLM.PROVIDER
    ZhiPu = ZhiPuLLM.PROVIDER
    MOONSHOT = MoonShotLLM.PROVIDER
    OLLAMA = OllamaLLM.PROVIDER
    DOUBAO = DouBaoLLM.PROVIDER
    SILICON = SiliconFlowLLM.PROVIDER
    STEP = StepLLM.PROVIDER
    BAICHUAN = BaiChuanLLM.PROVIDER
    
    @classmethod
    def from_str(cls, value: str) -> 'LLMType':
        for member in cls:
            if member.value == value:
                return member
        return None

class LLMManager:
    @staticmethod
    def get_default_provider() -> str:
        return MoonShotLLM.PROVIDER
        return OpenAILLM.PROVIDER

    @staticmethod  
    def get_default_query_analyze_model() -> str:
        return MoonShotLLM.V1_8K
        return OpenAILLM.GPT35_TURBO

    @staticmethod
    def get_default_generate_model() -> str:
        return MoonShotLLM.V1_8K
        if settings.ENV == settings.PROD:
            return OpenAILLM.GPT4_O
        return OpenAILLM.GPT35_TURBO

    LLM_CLASSES: dict[LLMType, Type[BaseLLM]] = {
        LLMType.OPENAI: OpenAILLM,
        LLMType.DEEPSEEK: DeepSeekLLM,
        LLMType.WENXIN: WenxinLLM,
        LLMType.QWEN: QWenLLM,
        LLMType.ZhiPu: ZhiPuLLM,
        LLMType.MOONSHOT: MoonShotLLM,
        LLMType.OLLAMA: OllamaLLM,
        LLMType.DOUBAO: DouBaoLLM,
        LLMType.SILICON: SiliconFlowLLM,
        LLMType.STEP: StepLLM,
        LLMType.BAICHUAN: BaiChuanLLM
    }

    @staticmethod
    def create_llm(llm_type: LLMType, name: str, timeout: int=60) -> BaseLLM:
        llm_class = LLMManager.LLM_CLASSES[llm_type]
        return llm_class(name=name, timeout=timeout)

    @staticmethod  
    def create_message(role: str, content: str) -> Dict[str, Any]:
        return {"role": role, "content": content}

    tokenizer = None
    @classmethod
    def init_tokenizer(cls):
        model_path=settings.TOKENIZER_MODEL
        L.debug(f"init_tokenizer model_path:{model_path}")
        if cls.tokenizer is None:
            cls.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    @classmethod
    def get_message_token_length(cls, llm_type: LLMType, message: list[Dict[str, Any]]):
        text = ""
        for item in message:
            if item and item["content"] and isinstance(item["content"], str):
                text += item["content"]
        return cls.get_token_length(llm_type, text)

    @classmethod
    def get_token_length(cls, llm_type: LLMType, text: str):
        if llm_type in [LLMType.OPENAI, LLMType.OLLAMA]:
            return cls.get_token_length_tiktoken(text)
        # 忽略本地模型计算长度，粗略估计
        # return cls.get_token_length_zh(text)
        return int(len(text)*0.7)
        
    @classmethod
    def get_token_length_zh(cls, text):
        if not isinstance(text, str):
            return 0
        cls.init_tokenizer()
        tokens = cls.tokenizer.encode(text)
        return len(tokens)

    @classmethod
    def get_token_length_tiktoken(cls, text: str) -> int:
        encoding_name: str = "cl100k_base"
        if not isinstance(text, str):
            return 0
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))

class Model(BaseModel):
    provider: str
    name: str
    
    @field_validator('provider')
    def validate_provider(cls, v):
        llm_type = LLMType.from_str(v)
        if llm_type is None:
            raise ValueError(f"Provider {v} not supported")
        return llm_type
    
    class Config:
        use_enum_values = True
 