from aivc.utils.audio import calculate_pcm_duration,audio_file_to_base64

def test_calculate_pcm_duration(buffer):
    duration = calculate_pcm_duration(buffer)
    print(f"duration:{duration}")
    assert duration > 0

def test_audio_file_to_base64(file_path: str) -> str:
    base64_str = audio_file_to_base64(file_path)
    print(base64_str)
    assert base64_str != ""

if __name__ == "__main__":
    filename = "/Users/gaochao/Downloads/20241101140710_4ed98690-033c-4518-b1ec-f9d81701cf23.pcm"
    test_calculate_pcm_duration(filename)
