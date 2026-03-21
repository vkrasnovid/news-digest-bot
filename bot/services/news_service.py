import asyncio
import logging

from bot.clients import rss_client
from bot.config import RSS_WORLD, RSS_RUSSIA, RSS_RUSSIA_2, RSS_SARATOV, RSS_SARATOV_2
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
    results = await asyncio.gather(
        rss_client.fetch_feed(RSS_WORLD),
        rss_client.fetch_feed(RSS_RUSSIA),
        rss_client.fetch_feed(RSS_RUSSIA_2),
        rss_client.fetch_feed(RSS_SARATOV),
        rss_client.fetch_feed(RSS_SARATOV_2),
        return_exceptions=True,
    )

    # Normalize exceptions to None
    normalized = []
    labels = ["World", "Russia(Lenta)", "Russia(RBC)", "Saratov(MK)", "Saratov(NVersia)"]
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error("%s news fetch failed: %s", labels[i], r, exc_info=r)
            normalized.append(None)
        else:
            normalized.append(r)

    world_entries = normalized[0]
    # Merge Russia sources
    russia_entries = (normalized[1] or []) + (normalized[2] or []) or None
    # Merge Saratov sources
    saratov_entries = (normalized[3] or []) + (normalized[4] or []) or None

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
