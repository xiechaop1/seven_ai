from abc import ABC, abstractmethod
from aivc.tts.common import TTSRsp

class BaseTTS(ABC):
    def __init__(self, trace_sn: str = None):
        self.trace_sn = trace_sn

    @abstractmethod
    async def tts(self, text: str, audio_format:str, compression_rate:int) -> TTSRsp:
        pass
