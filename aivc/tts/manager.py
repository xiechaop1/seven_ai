from enum import Enum
from aivc.tts.providers.xunfei import XunFeiTTS
from aivc.tts.providers.doubao import DoubaoTTS
from typing import Type
from aivc.tts.base import BaseTTS

class TTSType(Enum):
    XUNFEI = XunFeiTTS
    DOUBAO = DoubaoTTS

    @classmethod
    def from_str(cls, value: str) -> 'TTSType':
        for member in cls:
            if member.value == value:
                return member
        return None
    

class TTSManager:
    @staticmethod
    def get_default_provider() -> str:
        return DoubaoTTS.PROVIDER

    TTS_CLASSES: dict[TTSType, Type[BaseTTS]] = {
        TTSType.XUNFEI: XunFeiTTS,
        TTSType.DOUBAO: DoubaoTTS
    }

    @staticmethod
    def create_tts(tts_type: TTSType = TTSType.DOUBAO, trace_sn: str = None) -> BaseTTS:
        tts_class = TTSManager.TTS_CLASSES[tts_type]
        return tts_class(trace_sn=trace_sn)