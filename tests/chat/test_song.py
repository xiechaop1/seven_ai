from aivc.chat.song import SongPlayer
import base64


def test_song_player():
    song_player = SongPlayer()
    return song_player.get_next_song("test")

def test_code_decode():
    song_file = SongPlayer().get_next_song()
    print(song_file)
    with open(song_file, 'rb') as audio_file:
        audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        # save to a file
        with open("audio_data.txt", "w") as f:
            f.write(audio_data)

def play_mp3():
    import pygame
    pygame.mixer.init()
    pygame.mixer.music.load(test_song_player())
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def play_mp3_v2():
    from playsound import playsound
    playsound(test_song_player())
    
def play_mp3_v3():
    from pydub import AudioSegment
    from pydub.playback import play
    song = AudioSegment.from_mp3(test_song_player())
    play(song)

if __name__ == '__main__':
    play_mp3_v3()
