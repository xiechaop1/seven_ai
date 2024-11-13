import websocket
from datetime import datetime
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from time import mktime
from concurrent.futures import ThreadPoolExecutor
import asyncio
import os
import uuid
from functools import partial
from aivc.config.config import L,settings
from aivc.tts.common import TTSRsp, XunFeiVoice


class XunFeiTTS:
    PROVIDER = "xunfei"

    APP_ID_ENV_KEY = "XUNFEI_APP_ID"
    API_KEY_ENV_KEY = "XUNFEI_API_KEY"
    API_SECRET_ENV_KEY = "XUNFEI_API_SECRET"

    STATUS_FIRST_FRAME = 0        # 第一帧的标识
    STATUS_CONTINUE_FRAME = 1    # 中间帧标识
    STATUS_LAST_FRAME = 2         # 最后一帧的标识

    def __init__(self):
        self.APPID = self.get_app_id()
        self.APIKey = self.get_api_key()
        self.APISecret = self.get_api_secret()
        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {
            "aue": "raw",
            "auf": "audio/L16;rate=16000",
            "vcn": XunFeiVoice.XUXIAOBAO.value,
            "tte": "utf8"
        }
        self.Data = {"status": self.STATUS_LAST_FRAME, "text": ""}
        self.executor = ThreadPoolExecutor(max_workers=2)

        os.makedirs(settings.OUTPUT_ROOT_PATH, exist_ok=True)

    def get_app_id(self) -> str:
        app_id = os.getenv(self.APP_ID_ENV_KEY)
        if not app_id:
            raise ValueError(f"Environment variable {self.APP_ID_ENV_KEY} is not set.")
        return app_id

    def get_api_key(self) -> str:
        api_key = os.getenv(self.API_KEY_ENV_KEY)
        if not api_key:
            raise ValueError(f"Environment variable {self.API_KEY_ENV_KEY} is not set.")
        return api_key

    def get_api_secret(self) -> str:
        api_secret = os.getenv(self.API_SECRET_ENV_KEY)
        if not api_secret:
            raise ValueError(f"Environment variable {self.API_SECRET_ENV_KEY} is not set.")
        return api_secret

    def create_url(self) -> str:
        """
        生成WebSocket连接URL，包含认证参数
        """
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接签名字符串
        signature_origin = "host: ws-api.xfyun.cn\n" 
        signature_origin += f"date: {date}\n"
        signature_origin += "GET /v2/tts HTTP/1.1"

        # HMAC-SHA256加密
        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')

        # 拼接Authorization参数
        authorization_origin = (
            f'api_key="{self.APIKey}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha}"'
        )
        authorization = base64.b64encode(
            authorization_origin.encode('utf-8')
        ).decode('utf-8')

        # 生成最终URL
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        url = f"{url}?{urlencode(v)}"
        return url

    def on_message(self, ws, message):
        """
        处理接收到的消息
        """
        try:
            message = json.loads(message)
            code = message.get("code", -1)
            sid = message.get("sid", "")
            data = message.get("data", {})
            audio = data.get("audio", "")
            status = data.get("status", -1)

            # rsp_message = message.get("message", "")
            # ced = data.get("ced", "")
            # L.debug(f"讯飞语音合成on_message code:{code} rsp_message:{rsp_message} sid:{sid} status:{status} ced:{ced}")

            if code != 0:
                err_msg = message.get("message", "Unknown error")
                L.error(f"sid:{sid} 调用出错: {err_msg} 错误码:{code}")
                ws.close()
                return

            if audio:
                audio_data = base64.b64decode(audio)
                # 写入临时结果
                self.current_result.extend(audio_data)
                # L.debug(f"接收到音频数据, 长度: {len(audio_data)}")

            if status == self.STATUS_LAST_FRAME:
                L.info("接收完毕，关闭WebSocket连接。")
                ws.close()

        except Exception as e:
            L.error(f"解析消息时出错: {e}")
            ws.close()

    def on_error(self, ws, error):
        """
        处理WebSocket错误
        """
        L.error(f"WebSocket错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """
        处理WebSocket关闭
        """
        L.info("WebSocket连接关闭。")

    def on_open(self, ws, text: str):
        """
        当WebSocket连接建立时，开始发送文本数据
        """
        def run():
            self.Data["text"] = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            request_data = {
                "common": self.CommonArgs,
                "business": self.BusinessArgs,
                "data": self.Data
            }
            ws.send(json.dumps(request_data))
            L.debug(f"已发送文本数据: {text}")

        self.executor.submit(run)

    def get_filename(self):
        """
        生成唯一的文件名
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = uuid.uuid4()
        return f"{timestamp}_{unique_id}.pcm"

    async def tts(self, text: str) -> TTSRsp:
        """
        异步启动WebSocket连接并执行TTS
        """
        start_time = time.perf_counter()
        url = self.create_url()

        # 创建WebSocketApp
        ws_app = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        ws_app.on_open = lambda ws: self.on_open(ws, text)
        L.debug(f"开始连接到 {url} 进行TTS。text: {text}")

        # 初始化结果容器
        self.current_result = bytearray()

        loop = asyncio.get_event_loop()
        # 使用 functools.partial 来传递关键词参数
        run_forever_with_sslopt = partial(ws_app.run_forever, sslopt={"cert_reqs": ssl.CERT_NONE})
        future = loop.run_in_executor(self.executor, run_forever_with_sslopt)

        try:
            await future
        except Exception as e:
            L.error(f"TTS过程中出错: {e}")
            return TTSRsp(
                code=-1, 
                message=str(e), 
                input_size=len(text), 
                output_length=0, 
                price=0.0, 
                cost=int((time.perf_counter() - start_time) * 1000)
            )

        output_path = os.path.join(settings.OUTPUT_ROOT_PATH, self.get_filename())

        # 将接收到的音频数据写入文件
        try:
            with open(output_path, 'wb') as f:
                f.write(self.current_result)
            L.info(f"音频数据已保存到 {output_path} text: {text}")
        except Exception as e:
            L.error(f"保存音频数据时出错: {e} text: {text}")
            return TTSRsp(
                code=-1, 
                message=str(e), 
                input_size=len(text), 
                output_length=0, 
                price=0.0, 
                cost=int((time.perf_counter() - start_time) * 1000)
            )

        end_time = time.perf_counter()

        try:
            output_length = os.path.getsize(output_path)
        except Exception as e:
            L.error(f"获取输出文件大小时出错: {e} text: {text}")
            output_length = 0

        return TTSRsp(
            code=0,
            message="Success",
            text=text,
            audio_data=bytes(self.current_result),
            audio_format="pcm",
            sample_format="S16LE",
            bitrate=256000,
            channels=1,
            sample_rate=16000,
            audio_path=output_path,
            input_size=float(len(text)),
            output_length=output_length,
            price=0.0,  # 根据需求计算价格
            cost=int((end_time - start_time) * 1000)
        )