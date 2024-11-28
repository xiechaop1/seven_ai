from aivc.common.task_class import QuestionType
from aivc.config.config import settings
import os
from typing import Dict, NamedTuple

class SoundInfo(NamedTuple):
    sound_file: str
    text: str

class ActionSound:
    def __init__(self):
        self.action_sound_dict: Dict[str, SoundInfo] = {
            QuestionType.TAKE_PHOTO.value: SoundInfo(
                sound_file="take_photo.pcm",
                text="好的，我看一下"
            ),
        }
    
    def get_sound_info(self, action) -> SoundInfo:
        if action in self.action_sound_dict:
            sound_info = self.action_sound_dict[action]
            sound_path = os.path.join(settings.SOUND_DIR, sound_info.sound_file)
            return SoundInfo(
                sound_file=sound_path, 
                text=sound_info.text)
        return None