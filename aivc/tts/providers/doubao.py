import base64
import time
import os
import uuid
from aivc.config.config import settings,L
from aivc.tts.common import TTSRsp
from aivc.tts.base import BaseTTS
import aiohttp
import aiofiles
import json
from enum import Enum
from aivc.utils.id import get_filename

class DoubaoVoice(Enum):
    LANXIAOYANG = "BV426_streaming"     # 懒小羊
    CANCAN = "BV700_V2_streaming"       # BV700灿灿
    FEMALE = "BV001_V2_streaming"       # BV001通用女声
    MALE = "BV002_streaming"            # BV002通用男声
    GENTLE_FEMALE = "BV007_streaming"   # BV007亲切女声
    SUNNY_MALE = "BV056_streaming"      # BV056阳光男声
    LIVELY_FEMALE = "BV005_streaming"   # BV005活泼女声
    CUTE_CHILD = "BV051_streaming"      # BV051奶气萌娃  
    SISTER_BILINGUAL = "BV034_streaming"  # BV034知性姐姐-双语
    GENTLE_MALE = "BV033_streaming"     # BV033温柔小哥

class DoubaoTTS(BaseTTS):
    PROVIDER = "doubao"
    
    APP_ID_ENV_KEY = "DOUBAO_TTS_APP_ID"
    ACCESS_TOKEN_ENV_KEY = "DOUBAO_TTS_ACCESS_TOKEN"
    
    def __init__(self, trace_sn: str = None):
        self.trace_sn = trace_sn
        self.appid = self.get_app_id()
        self.access_token = self.get_access_token()
        self.cluster = "volcano_tts"
        
        self.voice_type = DoubaoVoice.LANXIAOYANG.value
        self.host = "openspeech.bytedance.com"
        self.api_url = f"https://{self.host}/api/v1/tts"
        
        self.headers = {
            "Authorization": f"Bearer;{self.access_token}"
        }
        
        os.makedirs(settings.OUTPUT_ROOT_PATH, exist_ok=True)

    def get_app_id(self) -> str:
        app_id = os.getenv(self.APP_ID_ENV_KEY)
        if not app_id:
            raise ValueError(f"Environment variable {self.APP_ID_ENV_KEY} is not set.")
        return app_id

    def get_access_token(self) -> str:
        access_token = os.getenv(self.ACCESS_TOKEN_ENV_KEY)
        if not access_token:
            raise ValueError(f"Environment variable {self.ACCESS_TOKEN_ENV_KEY} is not set.")
        return access_token

    def _build_request(self, text: str) -> dict:
        return {
            "app": {
                "appid": self.appid,
                "token": "seven_ai_token",
                "cluster": self.cluster
            },
            "user": {
                "uid": "seven_ai"
            },
            "audio": {
                "voice_type": self.voice_type,
                "encoding": "pcm",
                "rate": 16000,
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }

    async def tts(self, text: str) -> TTSRsp:
        try:
            start_time = time.perf_counter()
            
            request_json = self._build_request(text)
            L.debug(f"doubao tts req: {json.dumps(request_json, indent=2, ensure_ascii=False)} trace_sn:{self.trace_sn}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=request_json,
                    headers=self.headers
                ) as resp:
                    
                    if resp.status != 200:
                        return TTSRsp(
                            code=-1,
                            message=f"Request failed with status code: {resp.status}"
                        )
                    
                    resp_json = await resp.json()
                    
                    end_time = time.perf_counter()
                    
                    if "data" not in resp_json:
                        return TTSRsp(
                            code=-1, 
                            message="No data in response"
                        )
                    
                    audio_data = base64.b64decode(resp_json["data"])
                    output_path = os.path.join(settings.OUTPUT_ROOT_PATH, get_filename(trace_sn=self.trace_sn))

                    try:
                        async with aiofiles.open(output_path, "wb") as f:
                            await f.write(audio_data)
                            L.info(f"音频数据已保存到 {output_path} text: {text} trace_sn:{self.trace_sn}")
                    except Exception as e:
                        L.error(f"保存音频数据时出错: {e} text: {text} trace_sn:{self.trace_sn}")
                        return TTSRsp(
                            code=-1, 
                            message=str(e), 
                            input_size=len(text), 
                            output_length=0, 
                            price=0.0, 
                            cost=int((end_time - start_time) * 1000)
                        )
                        
                    return TTSRsp(
                        code=0,
                        message="Success", 
                        text=text,
                        audio_data=audio_data,
                        audio_format="pcm",
                        sample_format="S16LE",
                        bitrate=256000,
                        channels=1,
                        sample_rate=16000,
                        audio_path=output_path,
                        input_size=float(len(text)),
                        output_length=len(audio_data),
                        price=0.0,
                        cost=int((end_time - start_time) * 1000)
                    )
            
        except Exception as e:
            return TTSRsp(
                code=-1,
                message=f"Error occurred: {str(e)}"
            )