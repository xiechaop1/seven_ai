from aivc.tts.manager import TTSManager, TTSType
import asyncio

async def test_tts(tts_type: TTSType = TTSType.DOUBAO, compression_rate:int = 1):
    tts = TTSManager.create_tts(tts_type=tts_type)
    response = await tts.tts(
        text = "好的，我看一下",
        audio_format="mp3",
        compression_rate=compression_rate)
    if response.code == 0:
        print(f"TTS成功，音频文件保存在: {response.audio_path}, "
                f"音频数据大小: {response.output_length} bytes, "
                f"输入大小: {response.input_size} characters, "
                f"耗时: {response.cost} ms"
                f"compression_rate: {compression_rate}")
    else:
        print(f"TTS失败: {response.message}, 错误码: {response.code}")
    assert response.output_length > 0

if __name__ == "__main__":
    compression_rate = 10
    asyncio.run(test_tts(compression_rate=compression_rate))
