import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.services import digest_service
from bot.handlers.subscription import is_subscribed
from bot.config import CHAT_ID, DIGEST_HOURS, DIGEST_MINUTE, TIMEZONE

logger = logging.getLogger(__name__)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Configure and return the digest scheduler."""
    scheduler = AsyncIOScheduler()

    async def send_digest() -> None:
        if not is_subscribed(CHAT_ID):
            logger.info("Chat %s is unsubscribed, skipping digest", CHAT_ID)
            return

        logger.info("Sending scheduled digest to %s", CHAT_ID)
        try:
            messages = await digest_service.build_digest()
            for msg in messages:
                await bot.send_message(
                    CHAT_ID, msg, parse_mode="Markdown", disable_web_page_preview=True
                )
        except Exception as e:
            logger.error("Failed to send digest: %s", e)

    scheduler.add_job(
        send_digest,
        CronTrigger(hour=DIGEST_HOURS, minute=DIGEST_MINUTE, timezone=TIMEZONE),
        id="hourly_digest",
        name="Hourly news digest",
    )

    return scheduler
