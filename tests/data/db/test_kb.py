from aivc.chat.router import Router
from aivc.common.route import Route
from aivc.common.query_analyze import QueryAnalyzer


async def test_search_kb():
    result = await Router(
        route = Route(
            query_analyzer=QueryAnalyzer(
                question="包头天气怎么样"
            )
        )
    ).search_kb()
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_search_kb())

