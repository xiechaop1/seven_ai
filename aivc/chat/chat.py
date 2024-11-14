from aivc.common.chat import Prompt, ContentType
import time
from aivc.config.config import L, settings
from aivc.common.trace_tree import TraceTree
from aivc.text.parse import gen_text
from aivc.chat.llm.providers.deepseek import DeepSeekLLM
from aivc.chat.llm.providers.zhipu import ZhiPuLLM
# from aivc.chat.llm.providers.moonshot import MoonShotLLM
from aivc.chat.llm.manager import LLMManager,LLMType
import inspect
import traceback
from aivc.chat.llm.common import LLMRsp
from typing import AsyncGenerator
import re
from aivc.utils.message_dict import MessageDict
import json
import base64
from aivc.common.chat import Req, VCReqData

class Chat():
    def __init__(self, 
                llm_type:LLMType=LLMType.DEEPSEEK,
                model_name:str=DeepSeekLLM.DEEPSEEK_CHAT,
                timeout:int=60,
                prompt_style:str="thorough",
                content_type:str=ContentType.AUDIO.value):
        self.llm_type = llm_type
        self.model_name = model_name
        if content_type == ContentType.IMAGE.value:
            self.llm_type = LLMType.ZhiPu
            self.model_name = ZhiPuLLM.GLM_4V_PLUS
        self.llm = LLMManager.create_llm(self.llm_type, self.model_name, timeout)
        self.timeout = timeout
        self.prompt_style = prompt_style
        self.token_length_redundancy = 500

    async def gen_messages(self, 
                question: str, 
                related_data: str = "", 
                prompt: Prompt = Prompt(),
                conversation_id: str = "") -> list:
        result = gen_text(prompt.user, related_data=related_data, question=question)

        # 多轮对话
        messages = []
        L.debug(f"gen_messages conversation_id:{conversation_id}")
        if conversation_id:
            messages = await MessageDict().query(key=conversation_id)
            L.debug(f"gen_messages conversation_id:{conversation_id} MessageDict query messages:{messages}")
            
        if len(prompt.system.strip()) > 0:
            messages.append({"role": "system", "content": prompt.system})
        messages.append({"role": "user", "content": result})
        return messages

    async def gen_vision_messages(self, 
                img_path: str, 
                prompt: Prompt = Prompt(),
                conversation_id: str = "") -> list:
        messages = []
        with open(img_path, 'rb') as img_file:
            img_base = base64.b64encode(img_file.read()).decode('utf-8')
            content_list  = []
            if len(prompt.user.strip()) > 0:
                content_list.append({
                    "type": "text",
                    "text": prompt.user
                })
            content_list.append({
                "type": "image_url",
                "image_url": {
                    "url": img_base
                }
            })
            messages.append({"role": "user", "content": content_list})
            return messages
        return []

    async def chat_stream(self,
                question: str,
                related_data: str = "",
                trace_tree:TraceTree=TraceTree(),
                prompt:Prompt=Prompt(),
                file_path: str="",
                req: Req[VCReqData] = None) -> AsyncGenerator[str, None]:
        if req.data.content_type == ContentType.IMAGE.value:
            async for chunk_message in self.chat_stream_image(
                question=question,
                related_data=related_data,
                trace_tree=trace_tree,
                prompt=prompt,
                file_path=file_path,
                req=req):
                yield chunk_message
        else:
            async for chunk_message in self.chat_stream_text(
                question=question,
                related_data=related_data,
                trace_tree=trace_tree,
                prompt=prompt,
                file_path=file_path,
                req=req):
                yield chunk_message

    async def chat_stream_text(self,
                question: str,
                related_data: str = "",
                trace_tree:TraceTree=TraceTree(),
                prompt:Prompt=Prompt(),
                file_path: str="",
                req: Req[VCReqData] = None) -> AsyncGenerator[str, None]:
        start_time = time.perf_counter()
        messages = await self.gen_messages(
            question=question,
            related_data=related_data,
            prompt=prompt,
            conversation_id=trace_tree.root.conversation_id)
            
        prompt_tokens_local = LLMManager.get_message_token_length(
            llm_type=self.llm_type,
            message=messages)
        model_name = self.llm.select_model_by_length(
            length=prompt_tokens_local,
            model_name=self.model_name)  
        if model_name != self.model_name:
            self.llm = LLMManager.create_llm(self.llm_type, model_name, self.timeout)
            L.debug(f"chat_stream select_model_by_length trace_sn:{trace_tree.root.message_id} messages len:{len(messages)} prompt_tokens_local:{prompt_tokens_local} change model:{self.model_name}->{model_name}")
        L.debug(f"chat_stream start! trace_sn:{trace_tree.root.message_id} messages:{json.dumps(messages, indent=2, ensure_ascii=False)} prompt_tokens_local:{prompt_tokens_local}")

        i = 0
        answer = ""
        completion_tokens_local = 0

        try:
            async for chunk_message in self.llm.async_req_stream(messages=messages):
                duration =  int((time.perf_counter() - start_time) * 1000)
                if chunk_message and isinstance(chunk_message, str):
                    answer += chunk_message
                if i == 0:    
                    L.debug(f"chat_stream first rsp trace_sn:{trace_tree.root.message_id} cost:{duration}")
                i += 1

                if chunk_message is None:   
                    L.debug(f"chat_stream done trace_sn:{trace_tree.root.message_id} chunk_message:{chunk_message} answer:{answer} cost:{duration}")
                    completion_tokens_local = LLMManager.get_token_length(llm_type=self.llm_type, text=answer)
                    trace_tree.llm.model = model_name
                    trace_tree.llm.req_tokens = prompt_tokens_local
                    trace_tree.llm.resp_tokens = completion_tokens_local
                    trace_tree.llm.cost = duration
                    trace_tree.llm.price = self.llm.get_price(
                        input_tokens=prompt_tokens_local, 
                        output_tokens=completion_tokens_local)
                    trace_tree.llm.answer = answer
                    
                yield chunk_message
        except Exception as e:
            # 查找状态码
            error_attrs = inspect.getmembers(e)
            status_code = None
            for attr, value in error_attrs:
                if attr.lower() in ['status_code', 'code', 'status']:
                    status_code = value
                    break
            
            # status_code加文字判断(不同的模型可能有不同的错误信息)
            if status_code == 400 and "risk" in str(e):
                L.error(f"chat_stream error status_code:{status_code} trace_sn:{trace_tree.root.message_id} error:{e} stack_trace:{traceback.format_exc()}")
                yield "非常抱歉，由于检索到的某些信息触发了安全限制，暂时无法就此问题给出合适的回答。这并非您的问题有误，而是系统的判定可能过于严格。再次为带来不便致歉，建议您换一个问题，我们会尽力给出有帮助的回复。"
            else:
                L.error(f"chat_stream error trace_sn:{trace_tree.root.message_id} error:{e} stack_trace:{traceback.format_exc()}")
                yield settings.QA_NO_RESULT_RSP
        
        L.debug(f"chat_stream done trace_sn:{trace_tree.root.message_id} prompt_tokens_local:{prompt_tokens_local} completion_tokens_local:{completion_tokens_local} answer:{answer} cost:{round(time.time() - start_time, 3)}")
        yield None

    async def chat_stream_image(self,
                question: str,
                related_data: str = "",
                trace_tree:TraceTree=TraceTree(),
                prompt:Prompt=Prompt(),
                file_path: str="",
                req: Req[VCReqData] = None) -> AsyncGenerator[str, None]:
        
        start_time = time.perf_counter()
        messages = await self.gen_vision_messages(
                img_path=file_path,
                prompt=Prompt(user="你是一个儿童陪伴助手，用孩子能理解的语言，简洁明了的描述图片的内容。")
            )
        prompt_tokens_local = LLMManager.get_message_token_length(
            llm_type=self.llm_type,
            message=messages)
        L.debug(f"chat_stream_image start! trace_sn:{trace_tree.root.message_id} prompt_tokens_local:{prompt_tokens_local} llm_type:{self.llm_type} model_name:{self.model_name}")

        i = 0
        rsp_text = ""
        completion_tokens_local = 0

        try:
            async for chunk_message in self.llm.async_req_stream(messages=messages):
                duration =  int((time.perf_counter() - start_time) * 1000)
                if chunk_message and isinstance(chunk_message, str):
                    rsp_text += chunk_message
                if i == 0:    
                    L.debug(f"chat_stream first rsp trace_sn:{trace_tree.root.message_id} cost:{duration}")
                i += 1

                if not chunk_message:
                    L.debug(f"chat_stream done trace_sn:{trace_tree.root.message_id} chunk_message:{chunk_message} cost:{duration}")
                    completion_tokens_local = LLMManager.get_token_length(llm_type=self.llm_type, text=rsp_text)
                    trace_tree.llm.model = self.model_name
                    trace_tree.llm.req_tokens = prompt_tokens_local
                    trace_tree.llm.resp_tokens = completion_tokens_local
                    trace_tree.llm.cost = duration
                    trace_tree.llm.price = self.llm.get_price(
                        input_tokens=prompt_tokens_local, 
                        output_tokens=completion_tokens_local)

                yield chunk_message
        except Exception as e:
            # 查找状态码
            error_attrs = inspect.getmembers(e)
            status_code = None
            for attr, value in error_attrs:
                if attr.lower() in ['status_code', 'code', 'status']:
                    status_code = value
                    break
            
            # status_code加文字判断(不同的模型可能有不同的错误信息)
            if status_code == 400 and "risk" in str(e):
                L.error(f"chat_stream error status_code:{status_code} trace_sn:{trace_tree.root.message_id} error:{e} stack_trace:{traceback.format_exc()}")
                yield "非常抱歉，由于检索到的某些信息触发了安全限制，暂时无法就此问题给出合适的回答。这并非您的问题有误，而是系统的判定可能过于严格。再次为带来不便致歉，建议您换一个问题，我们会尽力给出有帮助的回复。"
            else:
                L.error(f"chat_stream error trace_sn:{trace_tree.root.message_id} error:{e} stack_trace:{traceback.format_exc()}")
                yield settings.QA_NO_RESULT_RSP
        
        L.debug(f"chat_stream done trace_sn:{trace_tree.root.message_id} prompt_tokens_local:{prompt_tokens_local} completion_tokens_local:{completion_tokens_local} cost:{round(time.time() - start_time, 3)}")
        yield None


    async def chat_stream_by_sentence(
        self,
        question: str,
        trace_tree: TraceTree = TraceTree(),
        min_sentence_length: int = 20,
        file_path: str = "",
        req: Req[VCReqData] = None) -> AsyncGenerator[str, None]:
        """
        通过 chat_stream 生成的消息流，按句子拆分并输出
        """
        buffer = ''
        accumulated_sentence = ''  
        first_sentence = True  

        # 匹配以指定标点符号结尾的句子
        sentence_end_re = re.compile(
            r'(?<![("\[])(.*?)([.?!。？！，：]|\.{3,}|\n)(?![")\]])'
        )
        # 正则表达式，检查句子中是否包含至少一个中英文字符
        valid_sentence_re = re.compile(r'[A-Za-z\u4e00-\u9fff]')

        async for chunk in self.chat_stream(
            question=question, 
            trace_tree=trace_tree,
            file_path=file_path,
            req=req):
            if chunk is None:
                L.debug(f"chat_stream_by_sentence done trace_sn:{trace_tree.root.message_id} trunk:{chunk}")
                break
            if chunk:
                buffer += str(chunk)
                while True:
                    match = sentence_end_re.search(buffer)
                    if match:
                        # 提取完整的句子，包括末尾标点
                        sentence = match.group(1) + match.group(2)
                        sentence = sentence.strip()
                        # 更新缓冲区，移除已处理的句子
                        buffer = buffer[match.end():]

                        # 检查句子是否包含至少一个中英文字符
                        if valid_sentence_re.search(sentence):
                            if first_sentence:
                                # 第一个句子，忽略最小长度限制
                                yield sentence
                                first_sentence = False
                            else:
                                # 检查句子长度
                                if accumulated_sentence:
                                    # 已有累积的句子，拼接当前句子
                                    accumulated_sentence += sentence
                                    if len(accumulated_sentence) >= min_sentence_length:
                                        yield accumulated_sentence
                                        accumulated_sentence = ''
                                    # 如果仍不满足长度，继续累积
                                else:
                                    if len(sentence) >= min_sentence_length:
                                        yield sentence
                                    else:
                                        accumulated_sentence = sentence
                        # 如果句子不包含中英文字符，则忽略
                    else:
                        break
 

        # 处理最后剩余的 buffer，如果有未完成的句子
        if buffer.strip():
            # 提取剩余的句子（可能不以标点结尾）
            remaining_sentence = buffer.strip()
            if valid_sentence_re.search(remaining_sentence):
                if first_sentence:
                    # 第一个句子仍然存在，忽略长度限制
                    yield remaining_sentence
                else:
                    if accumulated_sentence:
                        accumulated_sentence += remaining_sentence
                    else:
                        accumulated_sentence = remaining_sentence

        # 如果有累积的句子，输出
        if accumulated_sentence:
            yield accumulated_sentence
        # 结束
        yield None

    async def chat(self,
                question: str,
                related_data: str = "",
                trace_tree:TraceTree=TraceTree()) -> LLMRsp:
        start_time = time.time()
        messages = await self.gen_messages(related_data, question)
        req_tokens_length = LLMManager.get_message_token_length(
            llm_type=self.llm_type,
            message=messages)
        model_name = self.llm.select_model_by_length(
            length=req_tokens_length,
            model_name=self.model_name)  
        if model_name != self.model_name:
            self.llm = LLMManager.create_llm(self.llm_type, model_name, self.timeout)
            L.debug(f"chat select_model_by_length trace_sn:{trace_tree.root.message_id} messages len:{len(messages)} req_tokens_length:{req_tokens_length} change model:{self.model_name}->{model_name}")
        L.debug(f"chat start! trace_sn:{trace_tree.root.message_id} messages len:{len(messages)} req_tokens_length:{req_tokens_length}")
        
        L.debug(f"chat start! trace_sn:{trace_tree.root.message_id} messages len:{len(messages)} req_tokens_length:{req_tokens_length}")
        rsp = await self.llm.async_req(messages=messages)
        rsp_token_length = rsp.output_tokens
        L.debug(f"chat done trace_sn:{trace_tree.root.message_id} req_tokens_length:{req_tokens_length} rsp_tokens:{rsp_token_length} cost:{round(time.time() - start_time, 3)}")
        return rsp
    
    
    
     