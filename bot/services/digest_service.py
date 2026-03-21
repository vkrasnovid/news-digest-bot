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
    error_count = 0

    # Block 1: Currencies + Stocks
    block1_parts = []
    if isinstance(rates, str):
        block1_parts.append(rates)
    else:
        if isinstance(rates, Exception):
            logger.error("Rates service failed: %s", rates, exc_info=rates)
        block1_parts.append("💱 Курсы валют: ⚠️ ошибка загрузки")
        error_count += 1
    if isinstance(stocks, str):
        block1_parts.append(stocks)
    else:
        if isinstance(stocks, Exception):
            logger.error("Stocks service failed: %s", stocks, exc_info=stocks)
        block1_parts.append("📊 Акции: ⚠️ ошибка загрузки")
        error_count += 1
    messages.append("\n\n".join(block1_parts))

    # Block 2 & 3: News
    if isinstance(news, tuple) and len(news) == 2:
        world_russia, saratov = news
        messages.append(world_russia)
        messages.append(saratov)
    else:
        if isinstance(news, Exception):
            logger.error("News service failed: %s", news, exc_info=news)
        messages.append("📰 Новости: ⚠️ ошибка загрузки")
        error_count += 1

    # BUG-014: Log warning when all data sources failed
    if error_count == 3:
        logger.warning("Digest contains only errors — all API calls failed")
    elif error_count > 0:
        logger.warning("Digest partially degraded — %d of 3 data sources failed", error_count)

    return messages
