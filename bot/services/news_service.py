import asyncio

from bot.clients import rss_client
from bot.config import RSS_WORLD, RSS_RUSSIA, RSS_SARATOV


def _format_entries(entries: list[dict] | None, limit: int) -> list[str]:
    """Format RSS entries into numbered list with links."""
    if not entries:
        return ["⚠️ Не удалось загрузить"]
    lines = []
    seen_titles: set[str] = set()
    for entry in entries:
        title = entry["title"]
        # Simple deduplication by normalized title
        normalized = title.lower().strip()
        if normalized in seen_titles:
            continue
        seen_titles.add(normalized)
        link = entry["link"]
        lines.append(f"• [{title}]({link})")
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
        world_entries = None
    if isinstance(russia_entries, Exception):
        russia_entries = None
    if isinstance(saratov_entries, Exception):
        saratov_entries = None

    # Block 2: World + Russia
    block2_lines = ["🌍 *Мир*\n"]
    block2_lines.extend(_format_entries(world_entries, 5))
    block2_lines.append("\n🇷🇺 *Россия*\n")
    block2_lines.extend(_format_entries(russia_entries, 5))

    # Block 3: Saratov
    block3_lines = ["🏙 *Саратов*\n"]
    block3_lines.extend(_format_entries(saratov_entries, 3))

    return "\n".join(block2_lines), "\n".join(block3_lines)


async def get_all_news() -> str:
    """Get all news as a single message (for /news command)."""
    world_russia, saratov = await get_news()
    return f"{world_russia}\n\n{saratov}"
