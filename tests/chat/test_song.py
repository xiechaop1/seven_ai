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

if __name__ == '__main__':
    test_code_decode()
