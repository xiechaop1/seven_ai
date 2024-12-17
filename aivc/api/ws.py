from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from aivc.config.config import L,settings
from aivc.common.chat import Req, VCMethod, Resp, VCReqData, VCRespData
from aivc.api.voice_chat import voice_chat_ws
import traceback
from aivc.common.trace_tree import TraceTree, TraceRoot
import typing
from datetime import datetime
import asyncio
from collections import defaultdict
import enum

router = APIRouter()

@router.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    L.info(f"WebSocket connected {websocket.client.host:}:{websocket.client.port}")

    running_tasks = defaultdict(dict)
    conversation_id = ""
    
    try:
        while True:
            try:
                req_data = await websocket.receive_json()
                conversation_id = req_data.get("conversation_id", "")
                message_id = req_data.get("message_id", "")
                method = req_data.get("method", "")

                if method != VCMethod.PING:
                    recv_msg_str = f"--*--ws message recv--*-- rmt: {websocket.client.host}:{websocket.client.port}"
                    if method == VCMethod.VOICE_CHAT:
                        req = Req[VCReqData](**req_data)
                        recv_msg_str += f"req: {req}"
                    L.debug(recv_msg_str)

                task = asyncio.create_task(process_request(websocket, req_data, running_tasks))
                running_tasks[conversation_id][message_id] = task

            except WebSocketDisconnect:
                L.info(f"WebSocket disconnected {websocket.client.host:}:{websocket.client.port}")
                break
            except Exception as e:
                L.error(f"ws unexpected error:\n{str(e)}\ntraceback:\n{traceback.format_exc()}")
                break
                
    except Exception as e:
        L.error(f"Unexpected error in WebSocket endpoint: {str(e)}\n{traceback.format_exc()}")
    finally:
        # 清理所有运行中的任务
        for conv_tasks in running_tasks.values():
            for task in conv_tasks.values():
                if not task.done():
                    task.cancel()
        if websocket.client_state.name != WebSocketState.DISCONNECTED.name:
            await websocket.close(code=1012, reason="WebSocket closed")
        L.info(f"WebSocket closed finally {websocket.client.host:}:{websocket.client.port} conversation_id: {conversation_id}")

class WebSocketState(enum.Enum):
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 2
    RESPONSE = 3

async def process_request(
    websocket: WebSocket, 
    req_data: dict, 
    running_tasks: defaultdict
):
    method = req_data.get("method", "")
    message_id = req_data.get("message_id", "")
    conversation_id = req_data.get("conversation_id", "")
    
    try:
        if method == VCMethod.VOICE_CHAT:
            req = Req[VCReqData](**req_data)
            trace_tree = TraceTree(
                root = TraceRoot(
                    client_addr=f"{websocket.client.host}:{websocket.client.port}",
                    method=req.method,
                    conversation_id=req.conversation_id,
                    message_id=req.message_id,
                    req_timestamp=req.timestamp
                )
            )
            
            async for resp in voice_chat_ws(req=req, trace_tree=trace_tree):
                if websocket.client_state.name == WebSocketState.CONNECTED.name:
                    await websocket.send_json(resp.model_dump())
                    L.debug(f"--*--ws message resp--*-- rmt: {websocket.client.host}:{websocket.client.port} message_id: {message_id} conversation_id: {conversation_id} resp: {resp}")

                    # 更新TTS响应的发送时间
                    for trace_tts_resp in trace_tree.tts.resp_list:
                        if resp and resp.data and isinstance(resp.data, VCRespData) and trace_tts_resp.stream_seq == resp.data.stream_seq:
                            trace_tts_resp.send_timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        else:
            resp = await handle_text_request(req_data)
            if websocket.client_state.name == WebSocketState.CONNECTED.name:
                send_json = resp.model_dump() if hasattr(resp, 'model_dump') else resp
                await websocket.send_json(send_json)
    except Exception as e:
        L.error(f"Error processing request: {str(e)}\n{traceback.format_exc()}")
        if websocket.client_state.name == WebSocketState.CONNECTED.name:
            error_resp = Resp(
                version=settings.VERSION1,
                method=method,
                conversation_id=conversation_id,
                message_id=message_id,
                code=500,
                message=str(e)
            )
            await websocket.send_json(error_resp.model_dump())
    finally:
        # 任务完成后清理
        if message_id in running_tasks[conversation_id]:
            del running_tasks[conversation_id][message_id]

async def handle_text_request(req_data: typing.Any) -> typing.Any:
    conversation_id = req_data.get("conversation_id", "")
    message_id = req_data.get("message_id", "")
    method = req_data.get("method", "")
    try:
        if method == VCMethod.TEXT_CHAT:
            req = Req[VCReqData](**req_data)
            resp = await text_chat(req)
        elif method == VCMethod.PING:
            resp = {
                "method": "pong",
            }
        else:
            L.warning(f"Unknown method: {method} conversation_id: {conversation_id} message_id: {message_id}")
            resp = Resp(version=settings.VERSION1, 
                        conversation_id=conversation_id,
                        message_id=message_id, 
                        code=400, 
                        message=f"Unknown method: {method}")
        return resp
    except Exception as e:
        L.exception(e)
        return Resp(version=settings.VERSION1, 
                    method=req.method, 
                    conversation_id=req.conversation_id,
                    message_id=req.message_id, 
                    code=500, 
                    message=str(e))

async def text_chat(req: Req) -> Resp:
    return Resp(version=req.version, 
                method=req.method, 
                conversation_id=req.conversation_id,
                message_id=req.message_id, 
                code=0, 
                message="success")