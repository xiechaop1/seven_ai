from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from aivc.config.config import L,settings
from aivc.common.chat import Req, VCMethod, Resp, VCReqData
from aivc.api.voice_chat import voice_chat_ws
import traceback
from aivc.utils.message_dict import MessageDict
from aivc.common.trace_tree import TraceTree, TraceRoot
import typing

router = APIRouter()

@router.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    L.info(f"WebSocket connected {websocket.client.host:}:{websocket.client.port}")

    conversation_id = ""
    try:
        while True:
            try:
                req_data = await websocket.receive_json()
                conversation_id = req_data.get("conversation_id", "")
                message_id = req_data.get("message_id", "")
                token = req_data.get("token", "")
                method = req_data.get("method", "")
                if method != VCMethod.PING:
                    L.debug(f"ws method: {method} conversation_id: {conversation_id} message_id: {message_id} token: {token} rmt: {websocket.client.host}:{websocket.client.port}")

                if method == VCMethod.VOICE_CHAT:
                    req = Req[VCReqData](**req_data)
                    L.debug(f"ws conversation_id: {req.conversation_id} message_id: {req.message_id} content_type:{req.data.content_type} content len: {len(req.data.content)}")
                    trace_tree = TraceTree(
                        root = TraceRoot(
                            client_addr=f"{websocket.client.host}:{websocket.client.port}",
                            method=req.method,
                            conversation_id=req.conversation_id,
                            message_id=req.message_id,
                            req_timestamp=req.timestamp
                        )
                    )
                    # 预处理

                    async for resp in voice_chat_ws(
                        req = req,
                        trace_tree = trace_tree,
                    ):
                        await websocket.send_json(resp.model_dump())
                        L.debug(f"ws resp: {resp}")
                else:
                    resp = await handle_request(req_data)
                    send_json = resp.model_dump() if hasattr(resp, 'model_dump') else resp
                    await websocket.send_json(send_json)
            except WebSocketDisconnect:
                L.info(f"WebSocket disconnected {websocket.client.host:}:{websocket.client.port}")
                break
            except Exception as e:
                L.error(f"ws unexpected error:\n{str(e)}\ntraceback:\n{traceback.format_exc()}")
                if not websocket.client_state.DISCONNECTED:
                    rsp = Resp(version=settings.VERSION1,
                                method=method,
                                conversation_id=conversation_id,
                                message_id=message_id,
                                code=500,
                                message="internal server error")
                    await websocket.send_json(rsp.model_dump())
                break
    except WebSocketDisconnect:
        L.info(f"WebSocket disconnected {websocket.client.host:}:{websocket.client.port}")
    except Exception as e:
        L.error(f"Unexpected error in WebSocket endpoint: {str(e)} traceback: {traceback.format_exc()}")
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=1011, reason=str(e))
    finally:
        if not websocket.client_state.DISCONNECTED:
            await websocket.close(code=1012, reason="WebSocket closed")
        await MessageDict().delete(conversation_id)
        L.info(f"WebSocket closed finally {websocket.client.host:}:{websocket.client.port} conversation_id: {conversation_id} clean MessageDict")

async def handle_request(req_data: typing.Any) -> typing.Any:
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