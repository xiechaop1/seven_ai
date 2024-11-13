import os
import random
from typing import Dict, List
from aivc.config.config import settings

class SongPlayer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SongPlayer, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        self.all_songs = []
        song_dir = settings.SONG_DIR
        for file in os.listdir(song_dir):
            if file.endswith(('.mp3')): 
                self.all_songs.append(os.path.join(song_dir, file))
                
        self.played_songs: Dict[str, List[str]] = {}
        
    def get_next_song(self, username: str="") -> str:
        if username not in self.played_songs:
            self.played_songs[username] = []
            
        if len(self.played_songs[username]) == len(self.all_songs):
            self.played_songs[username] = []
            
        available_songs = [song for song in self.all_songs 
                         if song not in self.played_songs[username]]
        
        next_song = random.choice(available_songs)
        
        self.played_songs[username].append(next_song)
        
        return next_song