from aivc.chat.chat import Chat
import asyncio
from aivc.common.chat import Req, VCReqData
from aivc.utils.id import get_id


async def test_chat_by_sentence(question="背首唐诗"):
    async for sentence in Chat().chat_stream_by_sentence(
            question=question,
            min_sentence_length=20,
            req=Req[VCReqData](
                method="text-chat",
                conversation_id=get_id(),
                message_id=get_id(),
                data=VCReqData(
                    content_type="audio",
                    content=question
                )
            ),):
        print(sentence)


if __name__ == "__main__":
    asyncio.run(test_chat_by_sentence())