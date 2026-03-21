import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.handlers import start, rates, stocks, news, digest, subscription
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.scheduler.jobs import setup_scheduler
from bot.clients import close_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set")

    # BUG-001/010/013: Use HTML parse mode globally instead of Markdown
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.message.middleware(ThrottlingMiddleware())

    dp.include_routers(
        start.router,
        rates.router,
        stocks.router,
        news.router,
        digest.router,
        subscription.router,
    )

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("Scheduler started — digest every 3h (8,11,14,17,20,23 MSK)")

    logger.info("Bot starting polling…")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await close_session()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
