import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.services import digest_service
from bot.handlers.subscription import get_all_subscribers
from bot.config import DIGEST_HOURS, DIGEST_MINUTE, TIMEZONE
from bot.utils.formatting import split_message

logger = logging.getLogger(__name__)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Configure and return the digest scheduler."""
    scheduler = AsyncIOScheduler()

    async def send_digest() -> None:
        # BUG-003: Send to ALL subscribers, not just CHAT_ID
        subscribers = get_all_subscribers()
        if not subscribers:
            logger.info("No subscribers, skipping digest")
            return

        logger.info("Sending scheduled digest to %d subscriber(s)", len(subscribers))
        try:
            messages = await digest_service.build_digest()
            for chat_id in subscribers:
                try:
                    for msg in messages:
                        for part in split_message(msg):
                            await bot.send_message(
                                chat_id, part, disable_web_page_preview=True
                            )
                except Exception as e:
                    logger.error("Failed to send digest to %s: %s", chat_id, e)
        except Exception as e:
            logger.error("Failed to build digest: %s", e)

    scheduler.add_job(
        send_digest,
        CronTrigger(hour=DIGEST_HOURS, minute=DIGEST_MINUTE, timezone=TIMEZONE),
        id="hourly_digest",
        name="Hourly news digest",
    )

    return scheduler
