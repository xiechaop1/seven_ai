from aivc.chat.llm.manager import LLMType, OpenAILLM, WenxinLLM, QWenLLM, ZhiPuLLM, MoonShotLLM, DeepSeekLLM, OllamaLLM
from aivc.chat.chat import Chat
from aivc.chat.llm.manager import LLMManager
import time
from aivc.config.config import L
import json
from aivc.utils.tools import remove_outside_curly_brackets
import asyncio

def generate_message(question="hello"):
    return Chat(
        llm_type=LLMType.OLLAMA,
        model_name=OllamaLLM.LLAMA3_CHATQA_8B,
    ).gen_messages(question=question)

def test_llm_req(llm_type=LLMType.OPENAI, name=OpenAILLM.GPT35_TURBO, question="", timeout=60):
    llm = LLMManager.create_llm(llm_type=llm_type , name=name, timeout=timeout)
    messages = generate_message(paragraph=question)
    response = llm.req(messages=messages)

    content = response.content
    L.debug(f"req_token:{response.input_tokens}, res_token:{response.output_tokens}, cost:{response.cost}")

    try:
        data = json.loads(remove_outside_curly_brackets(content))
        return data, response.cost
    except Exception as e:
        L.error(f"--*-- error --*-- :{e}")
        return -1, response.cost

async def test_llm_async_req(llm_type=LLMType.OPENAI, name=OpenAILLM.GPT35_TURBO, question="", timeout=60):
    start_time = time.time()
    llm = LLMManager.create_llm(llm_type=llm_type , name=name, timeout=timeout)
    messages = generate_message(question=question)
    response = ""
    i = 0
    cost = 0
    try:
        async for chunk_message in llm.async_req_stream(messages=messages):
            i += 1
            if i == 1:
                cost = round(time.time()-start_time, 3)
            if chunk_message:
                response += chunk_message
                print(f"chunk_message:{chunk_message}")
        data = json.loads(remove_outside_curly_brackets(response))
        return data, cost
    except Exception as e:
        L.error(f"--*-- error --*-- :{e}")
        return -1, round(time.time()-start_time, 3)


def test_llm(llm_type=LLMType.OPENAI, name=OpenAILLM.GPT35_TURBO, question=""):
    # result, cost = test_llm_req(llm_type=llm_type, name=name, question=question)
    # print(f"req result:{result}, cost:{cost}")
    result, cost = asyncio.run(test_llm_async_req(llm_type=llm_type, name=name, question=question))
    print(f"async req result:{result}, cost:{cost}")

def test_llm_openai(question: str=""):
    test_llm(llm_type=LLMType.OPENAI, name=OpenAILLM.GPT35_TURBO, question=question)

def test_llm_wenxin(question: str=""):
    test_llm(llm_type=LLMType.WENXIN, name=WenxinLLM.ERNIE_TINY, question=question)

def test_llm_qwen(question: str=""):
    test_llm(llm_type=LLMType.QWEN, name=QWenLLM.QWEN_LONG, question=question)

def test_llm_zhipu(question: str=""):
    test_llm(llm_type=LLMType.ZhiPu, name=ZhiPuLLM.GLM_3, question=question)

def test_llm_moonshot(question: str=""):
    test_llm(llm_type=LLMType.MOONSHOT, name=MoonShotLLM.V1_8K, question=question)

def test_llm_deepseek(question: str=""):
    test_llm(llm_type=LLMType.DEEPSEEK, name=DeepSeekLLM.DEEPSEEK_CHAT, question=question)

def test_llm_ollama(question: str=""):
    test_llm(llm_type=LLMType.OLLAMA, name=OllamaLLM.QWEN_1_5, question=question)


if __name__ == "__main__":
    question = "你好"
    test_llm_moonshot(question=question)
