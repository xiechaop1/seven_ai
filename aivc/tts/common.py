from pydantic import BaseModel
from typing import Optional
from enum import Enum
    
class TTSRsp(BaseModel):
    code: int = 0
    message: str = ""
    action: Optional[str] = None
    text: Optional[str] = None
    audio_format: Optional[str] = None
    sample_format: Optional[str] = None 
    bitrate: Optional[int] = None
    channels: Optional[int] = None
    sample_rate: Optional[int] = None
    audio_data: Optional[bytes] = b""
    stream_seq: int = 0
    status: int = 0
    audio_path: Optional[str] = None   
    input_size: float = 0.0            
    output_length: int = 0              
    price: float = 0.0                  
    cost: int = 0  

    def __str__(self):
        return f"code: {self.code}, message: {self.message}, text: {self.text}, audio_path: {self.audio_path}, stream_seq:{self.stream_seq}, input_size: {self.input_size}, output_length: {self.output_length}, price: {self.price}, cost: {self.cost}"                  


class XunFeiVoice(Enum):
    """
    讯飞语音合成（TTS）角色枚举类。
    """
    XUXIAOBAO = 'aisbabyxu'    # 讯飞许小宝
    FANGFANG = 'x4_xiaofang'    # 讯飞芳芳
    XIAOYAN = 'xiaoyan'        # 讯飞小燕
    MENGMENGHAPPY = 'x_mengmenghappy'    # 讯飞萌萌-高兴

    def __str__(self):
        return self.value
