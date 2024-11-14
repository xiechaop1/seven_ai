from aivc.tts.manager import TTSManager, TTSType
import asyncio

async def test_tts(tts_type: TTSType = TTSType.DOUBAO):
    tts = TTSManager.create_tts(tts_type=tts_type)
    response = await tts.tts("这是一张描绘森林中三个小动物在散步的插图。从左到右，第一个是小猪，它手里拿着一个蓝色的物品，可能是手机或钱包")
    if response.code == 0:
        print(f"TTS成功，音频文件保存在: {response.audio_path}, "
                f"音频数据大小: {response.output_length} bytes, "
                f"输入大小: {response.input_size} characters, "
                f"耗时: {response.cost} ms")
    else:
        print(f"TTS失败: {response.message}, 错误码: {response.code}")
    assert response.output_length > 0

if __name__ == "__main__":
    asyncio.run(test_tts())