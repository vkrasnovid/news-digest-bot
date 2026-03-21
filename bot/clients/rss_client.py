import aiohttp
import logging
import feedparser

from bot.config import HTTP_TIMEOUT

logger = logging.getLogger(__name__)


async def fetch_feed(url: str) -> list[dict] | None:
    """Fetch and parse an RSS feed. Returns list of entries or None on failure."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()

        feed = feedparser.parse(text)
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
