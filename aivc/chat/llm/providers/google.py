import os
import google.generativeai as genai
from aivc.chat.llm.base import BaseLLM
from aivc.chat.llm.common import PricingInfo, ModelInfo, LLMRsp
from typing import List, Dict, Any
from aivc.config.config import settings, L
import time
import asyncio
from functools import wraps

def async_generator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        for item in func(*args, **kwargs):
            yield item
    return wrapper

class GoogleLLM(BaseLLM):
    PROVIDER = "google"
    API_KEY_ENV = "GOOGLE_KEY"
    
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"
    GEMINI_15_FLASH = "gemini-1.5-flash"

    MODELS = {
        GEMINI_2_FLASH: ModelInfo(
            name=GEMINI_2_FLASH,
            context_size=128000,  # 128k tokens
            pricing=PricingInfo(
                input=0.30*settings.USD_TO_CNY/settings.M,
                output=0.35*settings.USD_TO_CNY/settings.M
            )
        ),
        GEMINI_15_FLASH: ModelInfo(
            name=GEMINI_15_FLASH,
            context_size=1000000,  # 1M tokens
            pricing=PricingInfo(
                input=0.10*settings.USD_TO_CNY/settings.M,
                output=0.15*settings.USD_TO_CNY/settings.M
            )
        )
    }

    def __init__(self, name: str, timeout=60):
        if name not in self.MODELS:
            raise ValueError(f"Model {name} not supported")
        self._name = name
        self._timeout = timeout
        
        genai.configure(api_key=self.get_api_key())
        self._model = genai.GenerativeModel(self._name)

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Convert chat messages to prompt string"""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"Human: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        return prompt.strip()

    def req(self, messages: List[Dict[str, Any]]) -> LLMRsp:
        start_time = time.time()
        prompt = self._convert_messages(messages)
        
        response = self._model.generate_content(prompt)
        
        # 估算token数量 (简单估算)
        input_tokens = len(prompt) // 4
        output_tokens = len(response.text) // 4

        result = LLMRsp(
            content=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            price=self.get_price(input_tokens, output_tokens),
            cost=round(time.time()-start_time, 3)
        )
        L.debug(f"google response:{result.content} model:{self._name}")
        return result

    def req_stream(self, messages: List[Dict[str, Any]]):
        prompt = self._convert_messages(messages)
        response = self._model.generate_content(prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    async def async_req(self, messages: List[Dict[str, Any]]) -> LLMRsp:
        return await asyncio.to_thread(self.req, messages)

    @async_generator
    def async_req_stream(self, messages: List[Dict[str, Any]]):
        return self.req_stream(messages)

    def get_api_key(self) -> str:
        return os.getenv(self.API_KEY_ENV)
    
    def context_size(self) -> int:
        return self.MODELS[self._name].context_size
    
    def pricing(self) -> PricingInfo:
        return self.MODELS[self._name].pricing
    
    def get_price(self, 
                input_tokens:int, 
                output_tokens:int) -> float:
        pricing = self.pricing()
        return pricing.input * input_tokens + pricing.output * output_tokens

    def select_model_by_length(self, length: int, model_name: str) -> str:
        model_context_length = self.MODELS[model_name].context_size
        if length <= model_context_length:
            return model_name
        # 如果超出上下文长度，默认使用 1.5 版本(支持更长上下文)
        return self.GEMINI_15_FLASH