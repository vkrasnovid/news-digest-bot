import asyncio
import logging
import feedparser

from bot.clients import get_session

logger = logging.getLogger(__name__)


async def fetch_feed(url: str) -> list[dict] | None:
    """Fetch and parse an RSS feed. Returns list of entries or None on failure."""
    try:
        session = await get_session()
        headers = {"User-Agent": "Mozilla/5.0 (compatible; NewsDigestBot/1.0)"}
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            text = await resp.text()

        # BUG-005: Run synchronous feedparser in a thread to avoid blocking the event loop
        feed = await asyncio.to_thread(feedparser.parse, text)
        if feed.bozo and not feed.entries:
            logger.warning("RSS parse error for %s: %s", url, feed.bozo_exception)
            return None

        entries = []
        for entry in feed.entries:
            entries.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
            })
        return entries
    except Exception as e:
        logger.error("RSS fetch error for %s: %s", url, e)
        return None
