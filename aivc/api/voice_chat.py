from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from fastapi.responses import StreamingResponse
import os
from typing import Optional,AsyncGenerator
from aivc.srt.manager import SRTManager
from aivc.utils.id import get_id
from aivc.srt.common import SRTRsp
from aivc.config.config import L,CANCELLATION_EVENTS, settings
from aivc.chat.chat import Chat
from aivc.common.trace_tree import TraceTree,TraceSRT,TraceTTS
from aivc.tts.manager import TTSManager
from aivc.tts.common import TTSRsp
from aivc.utils.audio import calculate_pcm_duration
import asyncio
import traceback
from aivc.common.chat import Req, VCReqData, Resp, VCRespData
import base64
from aivc.utils.message_dict import MessageDict
import json
import time
# from aivc.common.route import Route
# from aivc.common.query_analyze import QueryAnalyzer
# from aivc.chat.router import Router

router = APIRouter()

async def process_voice_conversation(
    file_path: str,
    trace_sn: str,
    audio_queue: asyncio.Queue,
    cancellation_event: asyncio.Event,
    trace_tree:TraceTree = TraceTree()):

    try:
        # 语音识别
        srt = SRTManager.create_srt()
        srt_rsp: SRTRsp = await srt.recognize(audio_path=file_path)
        
        trace_srt = TraceSRT(
            cost=srt_rsp.cost,
            code=srt_rsp.code,
            message=srt_rsp.message,
            text=srt_rsp.text)
        trace_tree.srt = trace_srt

        if srt_rsp.code != 0:
            L.error(f"voice_chat srt error trace_sn:{trace_sn} code:{srt_rsp.code} message:{srt_rsp.message}")
            rsp = TTSRsp(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=srt_rsp.message)
            await audio_queue.put(rsp)
            return
        L.debug(f"voice_chat srt success trace_sn:{trace_sn} text:{srt_rsp.text} cost:{srt_rsp.cost}")
        if len(srt_rsp.text.strip()) == 0:
            L.error(f"voice_chat识别不到有效内容, trace_sn:{trace_sn}")
            rsp = TTSRsp(
                code=status.HTTP_400_BAD_REQUEST,
                message="识别不到有效内容")
            await audio_queue.put(rsp)
            return

        # 问题预处理
        # route = Route(
        #     query_analyzer=QueryAnalyzer(
        #         question=srt_rsp.text
        #     )
        # )
        # await Router(route=route).router()
        # L.debug(f"voice_chat route trace_sn:{trace_sn} question:{srt_rsp.text} task_class:{route.task_class}")

        question = srt_rsp.text
        answer = ""
        chat_instance = Chat()
        llm_start_time = time.perf_counter()
        llm_index = 0
        async for llm_rsp_trunk in chat_instance.chat_stream_by_sentence(
                question=question,
                trace_tree=trace_tree):
            if llm_index == 0:
                trace_tree.llm.first_cost = int((time.perf_counter() - llm_start_time) * 1000)
            
            # 流结束
            if llm_rsp_trunk is None:
                L.debug(f"chat_stream_by_sentence done trace_sn:{trace_sn} llm_index:{llm_index} llm_rsp_trunk:{llm_rsp_trunk}")
                rsp = TTSRsp(
                    audio_data=b"",
                    stream_seq=-1)
                await audio_queue.put(rsp)
                break
            
            answer += llm_rsp_trunk
            llm_index += 1
            L.debug(f"chat_stream_by_sentence trace_sn:{trace_sn} llm_rsp_trunk:{llm_rsp_trunk}")
            
            # 检查是否需要中断
            if cancellation_event.is_set():
                L.info(f"voice_chat cancelled during processing trace_sn:{trace_sn}")
                break
            
            tts = TTSManager.create_tts()
            tts_rsp: TTSRsp = await tts.tts(text=llm_rsp_trunk)
            # 流状态
            tts_rsp.stream_seq = llm_index
            L.debug(f"tts done trace_sn:{trace_sn} tts_rsp:{tts_rsp} llm_index:{llm_index}")

            if llm_index == 1:
                trace_tree.tts = TraceTTS(first_cost=tts_rsp.cost)
                
            if tts_rsp.code != 0:
                L.error(f"tts error trace_sn:{trace_sn} code:{tts_rsp.code} message:{tts_rsp.message} audio_data len:{len(tts_rsp.audio_data)}")
                rsp = TTSRsp(
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message=tts_rsp.message)
                await audio_queue.put(rsp)
                return   
            
            # 等待队列有空位，再放入音频数据
            await audio_queue.put(tts_rsp)

        # 保存对话
        await MessageDict().insert(key=trace_tree.root.conversation_id,value={
                "role": "user",
                "content": question})
        await MessageDict().insert(key=trace_tree.root.conversation_id,value={
                "role": "assistant",
                "content": answer})
        message_dict_value = await MessageDict().query(key=trace_tree.root.conversation_id)
        L.debug(f"voice_chat MessageDict value:{json.dumps(message_dict_value, ensure_ascii=False)} conversation_id:{trace_tree.root.conversation_id}")
        await audio_queue.put(None) 
    except Exception as e:
        L.error(f"process_audio unexpected error trace_sn:{trace_sn} error:{e} stack:{traceback.format_exc()}")
        resp = TTSRsp(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e))  
        await audio_queue.put(resp)
    finally:
        trace_tree.root.srt_cost = trace_tree.srt.cost
        trace_tree.root.llm_first_cost = trace_tree.llm.first_cost
        trace_tree.root.tts_first_cost = trace_tree.tts.first_cost
        L.debug(f"trace_tree: {trace_tree}")
        CANCELLATION_EVENTS.pop(trace_sn, None)

async def voice_chat_ws(req: Req[VCReqData], trace_tree:TraceTree = None) -> AsyncGenerator[Resp, None]:
    audio_data_bytes = base64.b64decode(req.data.audio_data)
    try:
        file_path = await save_audio_file(audio_data_bytes, req.message_id)
        await validate_audio_file_size(file_path)
    except Exception as e:
        L.error(f"voice_chat HTTPException conversation_id:{req.conversation_id} message_id:{req.message_id} error:{e} stack:{traceback.format_exc()}")
        raise
    L.debug(f"voice_chat save file file_path:{file_path} conversation_id:{req.conversation_id} message_id:{req.message_id}")

    # 最大未消费数据为3
    audio_queue: asyncio.Queue[TTSRsp] = asyncio.Queue(maxsize=settings.AUDIO_QUEUE_MAXSIZE)

    # 取消事件
    cancellation_event = asyncio.Event()
    CANCELLATION_EVENTS[req.conversation_id] = cancellation_event

    async def process_voice_conversation_wrapper():
        try:
            await process_voice_conversation(
                file_path=file_path, 
                trace_sn=req.message_id, 
                audio_queue=audio_queue, 
                cancellation_event=cancellation_event, 
                trace_tree=trace_tree)
        except Exception as e:
            L.error(f"process_voice_conversation_wrapper error conversation_id:{req.conversation_id} message_id:{req.message_id} error:{e} stack:{traceback.format_exc()}")
            resp = TTSRsp(
                code=status.HTTP_400_BAD_REQUEST,
                message=str(e))
            await audio_queue.put(resp)

    async def send_audio_generator() -> AsyncGenerator[Resp, None]:
        try:
            while True:
                tts_rsp = await audio_queue.get()
                if tts_rsp is None:
                    L.debug(f"send_audio_generator rsp is none. conversation_id:{req.conversation_id} message_id:{req.message_id}")
                    break

                # 错误返回到客户端
                if tts_rsp.code != 0:
                    L.error(f"send_audio_generator got error code:{tts_rsp.code} message:{tts_rsp.message} conversation_id:{req.conversation_id} message_id:{req.message_id}")
                    resp = Resp(
                        version=req.version,
                        method=req.method,
                        conversation_id=req.conversation_id,
                        message_id=req.message_id,
                        code=tts_rsp.code,
                        message=tts_rsp.message)
                    yield resp
                    break

                audio_data_base64 = base64.b64encode(tts_rsp.audio_data).decode("utf-8")
                L.debug(f"send_audio_generator conversation_id:{req.conversation_id} message_id:{req.message_id} audio_data_base64 len:{len(audio_data_base64)} tts_rsp:{tts_rsp}")
                resp_data = VCRespData(text=tts_rsp.text,
                                audio_data=audio_data_base64,
                                stream_seq=tts_rsp.stream_seq,
                                sample_rate=16000,
                                channels=1,
                                sample_format="S16LE",
                                bitrate=256000)
                resp = Resp(
                    version=req.version,
                    method=req.method,
                    conversation_id=req.conversation_id,
                    message_id=req.message_id,
                    data=resp_data)
                yield resp

                duration = calculate_pcm_duration(buffer=tts_rsp.audio_data)
                await asyncio.sleep(duration)
        except asyncio.CancelledError:
            L.warning(f"audio_generator cancelled for conversation_id:{req.conversation_id} message_id:{req.message_id}")
            cancellation_event.set()
        finally:
            cancellation_event.set()
            CANCELLATION_EVENTS.pop(req.message_id, None)

    asyncio.create_task(process_voice_conversation_wrapper())
    async for resp in send_audio_generator():
        yield resp

@router.post("/voice-chat")
async def voice_chat(
    file: UploadFile = File(..., description="上传的音频文件"),
    trace_sn: Optional[str] = Form(None, description="追踪标识，若未提供则自动生成")
):
    """
    接口：通过上传的音频文件进行识别（POST请求）
    参数：
        - file (UploadFile): 上传的音频文件（必填）
        - trace_sn (str, 可选): 追踪标识，若未提供则自动生成
    返回：
        StreamingResponse，流式返回语音回复
    """
    trace_sn = trace_sn or get_id()
    content = await file.read()
    try:
        file_path = await save_audio_file(content, trace_sn)
        await validate_audio_file_size(file_path)
    except Exception as e:
        L.error(f"voice_chat HTTPException trace_sn:{trace_sn} error:{e} stack:{traceback.format_exc()}")
        raise
    L.debug(f"voice_chat save file file_path:{file_path} trace_sn:{trace_sn}")

    # 最大未消费数据为3
    audio_queue = asyncio.Queue(maxsize=settings.AUDIO_QUEUE_MAXSIZE)

    # 取消事件
    cancellation_event = asyncio.Event()
    CANCELLATION_EVENTS[trace_sn] = cancellation_event

    async def send_audio_generator() -> AsyncGenerator[bytes, None]:
        try:
            while True:
                audio_data = await audio_queue.get()
                if audio_data is None:
                    break
                yield audio_data
                duration = calculate_pcm_duration(buffer=audio_data)
                await asyncio.sleep(duration)
        except asyncio.CancelledError:
            L.warning(f"audio_generator cancelled for trace_sn:{trace_sn}")
            cancellation_event.set()
        finally:
            cancellation_event.set()
            CANCELLATION_EVENTS.pop(trace_sn, None)

    async def process_voice_conversation_wrapper():
        try:
            await process_voice_conversation(file_path, trace_sn, audio_queue, cancellation_event)
        except Exception as e:
            L.error(f"process_voice_conversation_wrapper error trace_sn:{trace_sn} error:{e} stack:{traceback.format_exc()}")
            rsp = TTSRsp(
                code=status.HTTP_400_BAD_REQUEST,
                message=str(e))
            await audio_queue.put(rsp)

    asyncio.create_task(process_voice_conversation_wrapper())

    return StreamingResponse(
        send_audio_generator(),
        media_type="audio/x-pcm",
        headers={
            "Content-Type": "audio/x-pcm",
            "Sample-Rate": "16000",
            "Channels": "1",
            "Sample-Format": "S16LE",
            "Bitrate": "256000"
        }
    )

### 取消任务的 RESTful Endpoint ###
@router.post("/cancel-voice-chat")
async def cancel_voice_chat(trace_sn: str):
    """
    取消指定 trace_sn 的 voice_chat 任务
    """
    cancellation_event = CANCELLATION_EVENTS.get(trace_sn)
    if cancellation_event:
        cancellation_event.set()
        return {"detail": f"已取消 trace_sn: {trace_sn} 的任务"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"没有找到 trace_sn: {trace_sn} 对应的任务"
        )

def get_filename(trace_sn: str) -> str:
    return f"{trace_sn}"

def get_file_extension(filename: str) -> str:
    return filename.split(".")[-1].lower()

async def validate_audio_file_size(filepath:str):
    """
    验证上传的音频文件大小是否符合要求。

    :param file: UploadFile 对象
    :raises HTTPException: 如果验证失败，抛出相应的 HTTPException
    """

    MAX_FILE_SIZE = 10 * 1024 * 1024  

    L.debug(f"validate_audio_file_size filepath:{filepath}")
    file_size = os.path.getsize(filepath)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过限制: {MAX_FILE_SIZE / (1024 * 1024)} MB",
        )

    return file_size

async def save_audio_file(file_data: bytes, trace_sn: str) -> str:
    """
    保存音频文件到指定路径。

    :param file_data: 上传的音频文件数据
    :param trace_sn: 追踪标识
    :return: 保存的文件路径
    """
    os.makedirs(settings.UPLOAD_ROOT_PATH, exist_ok=True)
    saved_filename = get_filename(trace_sn)
    file_path = os.path.join(settings.UPLOAD_ROOT_PATH, saved_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file_data)
    return file_path