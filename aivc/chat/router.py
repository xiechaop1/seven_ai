import asyncio
from aivc.config.config import L
from aivc.common.route import Route
import time
import traceback
from sqlmodel import Session
from aivc.data.db.pg_engine import engine
from aivc.model.embed.embed import EmbedModel
from aivc.common.kb import KBSearchResult
from typing import Optional
from aivc.data.db import kb
from aivc.chat.prompt_selector import PromptSelector


class Router:
    def __init__(self,
                route: Route):
        self.route = route

    async def router(self):
        start_time = time.perf_counter()
 
        kb_result = await self.search_kb()
        self.route.kb_result = kb_result
        L.debug(f"router question:{self.route.query_analyzer.question} kb_result:{kb_result} cost:{int((time.perf_counter() - start_time) * 1000)}ms")
        # 选择prompt
        self.route.prompt = PromptSelector(kb_result=kb_result).select()


    async def search_kb(self) -> Optional[KBSearchResult]:
        L.debug(f"search_kb question:{self.route.query_analyzer.question}")
        try:
            def sync_search():
                try:
                    with Session(engine) as session:
                        vector = EmbedModel().embed(self.route.query_analyzer.question)
                        return kb.search_similar_questions(
                            session=session,
                            vector=vector,
                            top_k=5
                        )
                except Exception as e:
                    L.error(f"search_kb sync_search error: {e}")
                    traceback.print_exc()
                    return None

            results = await asyncio.to_thread(sync_search)
            if results and len(results) > 0:
                return results[0]
            return None
                
        except Exception as e:
            L.error(f"search_kb error: {e}")
            traceback.print_exc()
            return None
