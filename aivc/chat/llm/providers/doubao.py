import os
from aivc.chat.llm.base import BaseLLM
from aivc.chat.llm.common import PricingInfo, ModelInfo, LLMRsp
from typing import List, Dict, Any
from aivc.config.config import settings,L
import time
from volcenginesdkarkruntime import Ark,AsyncArk
import volcenginesdkcore
import volcenginesdkark

class APIKey:
    def __init__(self, api_key: str, expire_time: int):
        self.api_key = api_key
        self.expire_time = expire_time

class DouBaoLLM(BaseLLM):
    PROVIDER = "doubao"
    ACCESS_KEY_ENV = "DOUBAO_ACCESS_KEY"
    SECRET_KEY_ENV = "DOUBAO_SECRET_KEY"

    doubao_api_key = APIKey(api_key="", expire_time=0)

    LITE_4K = "doubao-lite-4k"
    LITE_32K = "doubao-lite-32k"
    LITE_128K = "doubao-lite-128k"
    # PRO_4K = "pro-4k"
    # PRO_32K = "pro-32k"
    # PRO_128K = "pro-128k"

    MODELS_REQ_NAME = {
        LITE_4K: "ep-20241125151815-rxwpv",
        LITE_32K: "ep-20241125151620-4tpx9",
        LITE_128K: "ep-20241125151713-s74ff",
        # PRO_4K: "ep-20240520021038-pft6f",
        # PRO_32K: "ep-20240520021053-sznd6",
        # PRO_128K: "ep-20240520021109-x7nqr"
    }

    MODELS = {
        LITE_4K: ModelInfo(
            name=LITE_4K,
            context_size=4000,
            pricing=PricingInfo(
                input=0.3/settings.M,
                output=0.6/settings.M
            )
        ),
        LITE_32K: ModelInfo(
            name=LITE_32K,
            context_size=32000,
            pricing=PricingInfo(
                input=0.3/settings.M,
                output=0.6/settings.M
            )
        ),
        LITE_128K: ModelInfo(
            name=LITE_128K,
            context_size=128000,
            pricing=PricingInfo(
                input=0.8/settings.M,
                output=1/settings.M
            )
        ),
        # PRO_4K: ModelInfo(
        #     name=PRO_4K,
        #     context_size=4000,
        #     pricing=PricingInfo(
        #         input=0.8/settings.M,
        #         output=2/settings.M
        #     )
        # ),
        # PRO_32K: ModelInfo(
        #     name=PRO_32K,
        #     context_size=32000,
        #     pricing=PricingInfo(
        #         input=0.8/settings.M,
        #         output=2/settings.M
        #     )
        # ),
        # PRO_128K: ModelInfo(
        #     name=PRO_128K,
        #     context_size=128000,
        #     pricing=PricingInfo(
        #         input=5/settings.M,
        #         output=9/settings.M
        #     )
        # )
    }

    def __init__(self, name: str, timeout=60):
        if name not in self.MODELS:
            raise ValueError(f"Model {name} not supported")
        self._name = name
        self._timeout = timeout

        self._client = Ark(
            api_key=self.get_api_key(),
            timeout=self._timeout
        )

        self._async_client = AsyncArk(
            api_key=self.get_api_key(),
            timeout=self._timeout
        )

    def req(self, messages: List[Dict[str, Any]]) -> LLMRsp:
        start_time = time.time()
        response = self._client.chat.completions.create(
            model=self.get_req_name(),
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
            model=self.get_req_name(),
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
            model=self.get_req_name(),
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
            model=self.get_req_name(),
            messages=messages,
            stream=True)

        result = ""
        async for chunk in stream:
            chunk_content = chunk.choices[0].delta.content
            yield chunk_content
            if isinstance(chunk_content, str):
                result += chunk_content
        L.debug(f"{self.PROVIDER} async response:{result}  model:{self._name}")

    def get_access_key(self) -> str:
        return os.getenv(self.ACCESS_KEY_ENV)
    
    def get_secret_key(self) -> str:
        return os.getenv(self.SECRET_KEY_ENV)
    
    def context_size(self) -> int:
        return self.MODELS[self._name].context_size
    
    def pricing(self) -> PricingInfo:
        return self.MODELS[self._name].pricing
    
    def get_price(self, 
                input_tokens:int, 
                output_tokens:int) -> float:
        pricing = self.pricing()
        return pricing.input * input_tokens + pricing.output * output_tokens
    
    def get_api_key(self) -> str:
        unix_time = int(time.time()) + 2*24*3600 # 提前 2 天更新
        if self.doubao_api_key.expire_time > unix_time and self.doubao_api_key.api_key:
            return self.doubao_api_key.api_key
        
        api_key, expire_time = self.get_api_key_action()

        if api_key and expire_time:
            self.doubao_api_key.api_key = api_key
            self.doubao_api_key.expire_time = expire_time
            return self.doubao_api_key.api_key
        else:
            return ""

    def get_api_key_action(self) -> str:
        configuration = volcenginesdkcore.Configuration()
        configuration.ak = self.get_access_key()
        configuration.sk = self.get_secret_key()
        configuration.region = "cn-beijing"
        volcenginesdkcore.Configuration.set_default(configuration)

        api_instance = volcenginesdkark.ARKApi()
        get_api_key_request = volcenginesdkark.GetApiKeyRequest(
            duration_seconds=30*24*3600, # 时效为 30 天
            resource_type="endpoint",
            resource_ids=list(self.MODELS_REQ_NAME.values()),
        )
        
        try:
            resp = api_instance.get_api_key(get_api_key_request)
            resp_dict = resp.to_dict()
            return resp_dict.get("api_key"), resp_dict.get("expired_time")
        except Exception as e:
            L.error(f"get_doubao_key error:{e}")
            return "", 0
        
    def get_req_name(self) -> str:
        return self.MODELS_REQ_NAME[self._name]

    def select_model_by_length(self, length: int, model_name: str) -> str:
        model_context_size = self.MODELS[model_name].context_size
        if length <= model_context_size:
            return model_name
        else:
            if model_name.startswith("lite"):
                return self.LITE_128K
            else:
                return self.PRO_128K
