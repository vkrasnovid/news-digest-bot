import asyncio
import logging

from bot.clients import rss_client
from bot.config import RSS_WORLD, RSS_RUSSIA, RSS_SARATOV
from bot.utils.formatting import escape_html_text

logger = logging.getLogger(__name__)


def _format_entries(
    entries: list[dict] | None, limit: int, seen_titles: set[str]
) -> list[str]:
    """Format RSS entries into numbered list with HTML links.

    BUG-001/006: Use HTML <a> tags instead of Markdown links.
    BUG-015: Accept shared seen_titles set for cross-category dedup.
    """
    if not entries:
        return ["⚠️ Не удалось загрузить"]
    lines = []
    for entry in entries:
        title = entry["title"]
        normalized = title.lower().strip()
        if normalized in seen_titles:
            continue
        seen_titles.add(normalized)
        link = entry["link"]
        lines.append(f'• <a href="{escape_html_text(link)}">{escape_html_text(title)}</a>')
        if len(lines) >= limit:
            break
    return lines if lines else ["Нет новостей"]


async def get_news() -> tuple[str, str]:
    """Fetch and format news. Returns (world+russia block, saratov block)."""
    world_entries, russia_entries, saratov_entries = await asyncio.gather(
        rss_client.fetch_feed(RSS_WORLD),
        rss_client.fetch_feed(RSS_RUSSIA),
        rss_client.fetch_feed(RSS_SARATOV),
        return_exceptions=True,
    )

    # Normalize exceptions to None
    if isinstance(world_entries, Exception):
        logger.error("World news fetch failed: %s", world_entries, exc_info=world_entries)
        world_entries = None
    if isinstance(russia_entries, Exception):
        logger.error("Russia news fetch failed: %s", russia_entries, exc_info=russia_entries)
        russia_entries = None
    if isinstance(saratov_entries, Exception):
        logger.error("Saratov news fetch failed: %s", saratov_entries, exc_info=saratov_entries)
        saratov_entries = None

    # BUG-015: Shared deduplication set across all categories
    seen_titles: set[str] = set()

    # Block 2: World + Russia
    block2_lines = ["🌍 <b>Мир</b>\n"]
    block2_lines.extend(_format_entries(world_entries, 5, seen_titles))
    block2_lines.append("\n🇷🇺 <b>Россия</b>\n")
    block2_lines.extend(_format_entries(russia_entries, 5, seen_titles))

    # Block 3: Saratov
    block3_lines = ["🏙 <b>Саратов</b>\n"]
    block3_lines.extend(_format_entries(saratov_entries, 3, seen_titles))

    return "\n".join(block2_lines), "\n".join(block3_lines)


async def get_all_news() -> str:
    """Get all news as a single message (for /news command)."""
    world_russia, saratov = await get_news()
    return f"{world_russia}\n\n{saratov}"
