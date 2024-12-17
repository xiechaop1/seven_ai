from aivc.common.task_class import QuestionType
from aivc.config.config import settings
import os
from typing import Dict, NamedTuple
from enum import Enum

class AudioFormat(Enum):
    PCM = "pcm"
    OGG_OPUS = "ogg_opus"
    MP3 = "mp3"

class SoundInfo(NamedTuple):
    text: str
    sound_files: Dict[str, str] = {}
    selected_sound_file: str = None

class ActionSound:
    def __init__(self):
        self.action_sound_dict: Dict[str, SoundInfo] = {
            QuestionType.TAKE_PHOTO.value: SoundInfo(
                sound_files={
                    AudioFormat.PCM.value: "take_photo.pcm",
                    AudioFormat.OGG_OPUS.value: "take_photo.ogg_opus",
                    AudioFormat.MP3.value: "take_photo.mp3"
                },
                text="好的，我看一下"
            ),
        }
    
    def get_sound_info(self, action, format: str = AudioFormat.PCM.value ) -> SoundInfo:
        if action in self.action_sound_dict:
            sound_info = self.action_sound_dict[action]
            if format in sound_info.sound_files:
                sound_path = os.path.join(settings.SOUND_DIR, sound_info.sound_files[format])
                return SoundInfo(
                    selected_sound_file=sound_path,
                    text=sound_info.text)
        return None