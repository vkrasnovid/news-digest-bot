import logging

from bot.clients.newsapi_client import search_news
from bot.utils.formatting import escape_html_text

logger = logging.getLogger(__name__)


async def get_details(topic: str) -> str:
    """Fetch and format news articles for the given topic."""
    articles = await search_news(topic, page_size=5)

    if not articles:
        return f'Новостей по теме «{escape_html_text(topic)}» не найдено'

    safe_topic = escape_html_text(topic)
    lines = [f'🔎 <b>Подробности: {safe_topic}</b>\n']

    for art in articles[:5]:
        title = escape_html_text(art.get("title") or "Без заголовка")
        description = escape_html_text(art.get("description") or "")
        url = art.get("url") or ""
        lines.append(f'▪ <a href="{url}">{title}</a>')
        if description:
            lines.append(f'  {description}')
        lines.append("")

    return "\n".join(lines).strip()
