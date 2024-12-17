from aivc.chat.llm.base import BaseLLM
from aivc.chat.llm.common import PricingInfo, ModelInfo, LLMRsp
from openai import OpenAI,AsyncOpenAI
from typing import List, Dict, Any
import time
from aivc.config.config import L, settings, CPU, MPS
from transformers import AutoModelForCausalLM, AutoTokenizer

class OllamaLLM(BaseLLM):
    req_type_http = "http"
    req_type_local = "local"

    model = None
    tokenizer = None

    PROVIDER = "ollama"
    base_url = "http://192.168.0.19:11434/v1/"
    # required but ignored
    API_KEY = "ollama" 

    # https://ollama.com/library/llama3-chatqa
    LLAMA3_CHATQA_8B = "llama3-chatqa:latest"
    # https://ollama.com/library/command-r
    COMMAND_R = "command-r:latest"
    # https://ollama.com/library/qwen2.5:0.5b
    QWEN_25_05B = "qwen2.5:0.5b"
    QWEN_25_3B = "qwen2.5:3b"

    MODELS = {
        LLAMA3_CHATQA_8B: ModelInfo(
            name=LLAMA3_CHATQA_8B,
            context_size=8000-2000,
            pricing=PricingInfo(
                input=0,
                output=0
            )
        ),
        COMMAND_R: ModelInfo(
            name=COMMAND_R,
            context_size=128000-2000,
            pricing=PricingInfo(
                input=0,
                output=0
            )
        ),
        QWEN_25_05B: ModelInfo(
            name=QWEN_25_05B,
            context_size=128000-2000,
            pricing=PricingInfo(
                input=0,
                output=0
            )
        ),
        QWEN_25_3B: ModelInfo(
            name=QWEN_25_3B,
            context_size=128000-2000,
            pricing=PricingInfo(
                input=0,
                output=0
            )
        )
        }

    def __init__(self, name: str, timeout=60, req_type=req_type_http):
        if name not in self.MODELS:
            raise ValueError(f"Model {name} not supported")
        self._name = name
        self._timeout = timeout
        self.req_type = req_type

        if self.req_type == self.req_type_http:
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
        elif self.req_type == self.req_type_local:
            self.load_model()

    @classmethod
    def load_model(cls):
        if cls.model is None or cls.tokenizer is None:
            try:
                cls.model = AutoModelForCausalLM.from_pretrained(
                    cls.MODELS[cls.QWEN_1_5].local_path,
                    torch_dtype="auto",
                    device_map="auto"
                )
                cls.tokenizer = AutoTokenizer.from_pretrained(
                    cls.MODELS[cls.QWEN_1_5].local_path
                )
                L.info(f"Model: {cls.QWEN_1_5} loaded")
            except Exception as e:
                L.error(f"Failed to load model: {cls.QWEN_1_5} error:{str(e)}")

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
            chunk_content = chunk.choices[0].delta.content
            yield chunk_content
            if isinstance(chunk_content, str):
                result += chunk_content
        L.debug(f"{self.PROVIDER} async response:{result}  model:{self._name}")

    def get_api_key(self) -> str:
        return self.API_KEY
    
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
        model_context_size = self.MODELS[model_name].context_size
        if length <= model_context_size:
            return model_name
        else:
            if model_name == self.LLAMA3_CHATQA_8B:
                return self.COMMAND_R
        return model_name

    def req_local(self, messages: List[Dict[str, Any]]) -> LLMRsp:
        start_time = time.time()
        
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        device = settings.DEVICE
        if device == MPS:
            device = CPU
        model_inputs = self.tokenizer([text], return_tensors="pt").to(device)

        input_tokens = len(model_inputs.input_ids[0])

        generated_ids = self.model.generate(
            model_inputs.input_ids,
            max_new_tokens=512
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        output_tokens = len(generated_ids[0])

        result = LLMRsp(
            content=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            price=self.get_price(input_tokens, output_tokens),
            cost=round(time.time()-start_time, 3)
        )
        L.debug(f"{self.PROVIDER} response:{result.content}  model:{self._name}")
        return result
