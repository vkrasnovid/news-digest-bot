import logging

from bot.clients import get_session
from bot.config import NEWSAPI_KEY

logger = logging.getLogger(__name__)

NEWSAPI_URL = "https://newsapi.org/v2/everything"


async def search_news(topic: str, page_size: int = 5) -> list[dict]:
    """Search NewsAPI for articles matching the topic."""
    session = await get_session()
    params = {
        "q": topic,
        "language": "ru,en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWSAPI_KEY,
    }
    async with session.get(NEWSAPI_URL, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()

    articles = data.get("articles") or []
    return articles
