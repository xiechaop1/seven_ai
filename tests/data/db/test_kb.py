from aivc.data.db import kb
from aivc.data.db.pg_engine import engine
from sqlmodel import Session
from aivc.model.embed.embed import EmbedModel

def search_kb():
    with Session(engine) as session:
        vector = EmbedModel().embed("唱儿歌")
        results = kb.search_similar_questions(
            session=session,
            vector=vector,
            top_k=5
        )
        for result in results:
            print(result)

if __name__ == '__main__':
    search_kb()