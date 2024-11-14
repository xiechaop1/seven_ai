import os
from aivc.chat.llm.base import BaseLLM
from aivc.chat.llm.common import PricingInfo, ModelInfo, LLMRsp
from zhipuai import ZhipuAI
from typing import List, Dict, Any
import time
from aivc.config.config import settings, L
import asyncio

class ZhiPuLLM(BaseLLM):
    base_url = "https://open.bigmodel.cn/api/paas/v4/"
    PROVIDER = "zhipu"
    API_KEY_ENV = "ZHIPU_KEY"

    GLM_4 = "glm-4"
    GLM_3 = "glm-3-turbo"
    GLM_4V_PLUS = "glm-4v-plus"


    MODELS = {
        GLM_4: ModelInfo(
            name=GLM_4,
            context_size=128000-2000,
            pricing=PricingInfo(
                input=100/settings.M,
                output=100/settings.M
            )
        ),
        GLM_3: ModelInfo(
            name=GLM_3,
            context_size=128000-2000,
            pricing=PricingInfo(
                input=1/settings.M,
                output=1/settings.M
            )
        ),
        GLM_4V_PLUS: ModelInfo(
            name=GLM_4V_PLUS,
            context_size=128000-2000,
            pricing=PricingInfo(
                input=10/settings.M,
                output=10/settings.M
            )
        )
        }

    def __init__(self, name: str, timeout=60):
        if name not in self.MODELS:
            raise ValueError(f"Model {name} not supported")
        self._name = name
        self._timeout = timeout

        self._client = ZhipuAI(
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
        response = self._client.chat.asyncCompletions.create(
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
        # stream = self._client.chat.asyncCompletions.create(
        #     model=self._name,
        #     messages=messages,
        #     stream=True)
        stream = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self._name,
                messages=messages,
                stream=True
            )
        result = ""
        for chunk in stream:
            chunk_content = chunk.choices[0].delta.content
            yield chunk_content
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