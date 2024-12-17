import os
from aivc.chat.llm.base import BaseLLM
from aivc.chat.llm.common import PricingInfo, ModelInfo, LLMRsp
from openai import OpenAI,AsyncOpenAI
from typing import List, Dict, Any
from aivc.config.config import settings,L
import time
 
class BaiChuanLLM(BaseLLM):
    PROVIDER = "baichuan"
    API_KEY_ENV = "BAICHUAN_KEY"
    base_url = "https://api.baichuan-ai.com/v1/"

    BAICHUAN4_TURBO = "Baichuan4-Turbo"
    BAICHUAN4_AIR = "Baichuan4-Air"

    MODELS = {
        BAICHUAN4_TURBO: ModelInfo(
            name=BAICHUAN4_TURBO,
            context_size=32000-2000,
            pricing=PricingInfo(
                input=15/settings.M,
                output=15/settings.M
            )
        ),
        BAICHUAN4_AIR: ModelInfo(
            name=BAICHUAN4_AIR,
            context_size=32000-2000,
            pricing=PricingInfo(
                input=0.98/settings.M,
                output=0.98/settings.M
            )
        )
    }


    def __init__(self, name: str, timeout=60):
        if name not in self.MODELS:
            raise ValueError(f"Model {name} not supported")
        self._name = name
        self._timeout = timeout

        self._client = OpenAI(
            api_key = self.get_api_key(),
            base_url=self.base_url,
            timeout=self._timeout
        )

        self._async_client = AsyncOpenAI(
            api_key = self.get_api_key(),
            base_url=self.base_url,
            timeout=self._timeout
        )

    def req(self, messages: List[Dict[str, Any]]) -> LLMRsp:
        start_time = time.time()
        response = self._client.chat.completions.create(
            model=self._name,
            messages=messages)

        input_tokens=response.usage.prompt_tokens
        output_tokens=response.usage.completion_tokens
        result = LLMRsp(
            content=response.choices[0].message.content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            price=self.get_price(input_tokens, output_tokens),
            cost=round(time.time()-start_time, 3)
        )
        L.debug(f"{self.PROVIDER} response:{result.content}  model:{self._name}")
        return result

    def req_stream(self, messages: List[Dict[str, Any]]):
        stream = self._client.chat.completions.create(
            model=self._name,
            messages=messages,
            stream=True)

        result = ""
        for chunk in stream:
            chunk_content = chunk.choices[0].delta.content
            yield chunk_content
            if isinstance(chunk_content, str):
                result += chunk_content
        L.debug(f"{self.PROVIDER} response:{result}  model:{self._name}")

    async def async_req(self, messages: List[Dict[str, Any]]) -> LLMRsp:
        start_time = time.time()
        response = await self._async_client.chat.completions.create(
            model=self._name,
            messages=messages)
        
        input_tokens=response.usage.prompt_tokens
        output_tokens=response.usage.completion_tokens
        result = LLMRsp(
            content=response.choices[0].message.content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            price=self.get_price(input_tokens, output_tokens),
            cost=round(time.time()-start_time, 3)
        )
        L.debug(f"{self.PROVIDER} async response:{result.content}  model:{self._name}")
        return result

    async def async_req_stream(self, messages: List[Dict[str, Any]]):
        stream = await self._async_client.chat.completions.create(
            model=self._name,
            messages=messages,
            stream=True)

        result = ""
        async for chunk in stream:
            choice = chunk.choices[0]
            chunk_content = choice.delta.content
            finish_reason = choice.finish_reason
            # L.debug(f"{self.PROVIDER} async chunk:{chunk_content}")
            yield chunk_content
            # 如果是最后一个chunk，结束循环
            if finish_reason is not None:
                L.debug(f"{self.PROVIDER} async finish_reason:{finish_reason}")
                yield None
                break
            if isinstance(chunk_content, str):
                result += chunk_content
        L.debug(f"{self.PROVIDER} async response:{result}  model:{self._name}")

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
        return model_name