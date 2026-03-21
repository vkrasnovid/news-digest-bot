import asyncio
import logging

from bot.services import rates_service, stocks_service, news_service

logger = logging.getLogger(__name__)


async def build_digest() -> list[str]:
    """Build 3 message blocks for the full digest.

    Block 1: Currencies + Gold + Stocks
    Block 2: World + Russia news
    Block 3: Saratov news
    """
    rates, stocks, news = await asyncio.gather(
        rates_service.get_rates(),
        stocks_service.get_stocks(),
        news_service.get_news(),
        return_exceptions=True,
    )

    messages = []

    # Block 1: Currencies + Stocks
    block1_parts = []
    block1_parts.append(rates if isinstance(rates, str) else "💱 Курсы валют: ⚠️ ошибка загрузки")
    block1_parts.append(stocks if isinstance(stocks, str) else "📊 Акции: ⚠️ ошибка загрузки")
    messages.append("\n\n".join(block1_parts))

    # Block 2 & 3: News
    if isinstance(news, tuple) and len(news) == 2:
        world_russia, saratov = news
        messages.append(world_russia)
        messages.append(saratov)
    else:
        messages.append("📰 Новости: ⚠️ ошибка загрузки")

    return messages
