import json
import logging
import os
import tempfile

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.config import CHAT_ID, SUBSCRIBERS_FILE

router = Router()
logger = logging.getLogger(__name__)

# BUG-008: Persist subscriptions to file
_subscribed_chats: set[int] = set()
_initialized: bool = False


def _load_subscribers() -> None:
    """Load subscribers from JSON file, falling back to default CHAT_ID."""
    global _initialized
    if _initialized:
        return
    _initialized = True
    if os.path.exists(SUBSCRIBERS_FILE):
        try:
            with open(SUBSCRIBERS_FILE, "r") as f:
                data = json.load(f)
            _subscribed_chats.update(data)
            logger.info("Loaded %d subscribers from %s", len(_subscribed_chats), SUBSCRIBERS_FILE)
            return
        except Exception as e:
            logger.error("Failed to load subscribers: %s", e)
    # First run or corrupted file: seed with default CHAT_ID
    _subscribed_chats.add(CHAT_ID)
    _save_subscribers()


def _save_subscribers() -> None:
    """Persist current subscribers to JSON file atomically."""
    try:
        dir_name = os.path.dirname(os.path.abspath(SUBSCRIBERS_FILE))
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(sorted(_subscribed_chats), f)
            os.replace(tmp_path, SUBSCRIBERS_FILE)
        except BaseException:
            os.unlink(tmp_path)
            raise
    except Exception as e:
        logger.error("Failed to save subscribers: %s", e)


def is_subscribed(chat_id: int) -> bool:
    _load_subscribers()
    return chat_id in _subscribed_chats


def get_all_subscribers() -> set[int]:
    """Return a copy of all subscribed chat IDs."""
    _load_subscribers()
    return set(_subscribed_chats)


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    _load_subscribers()
    if message.chat.id in _subscribed_chats:
        await message.answer("✅ Вы уже подписаны на рассылку дайджеста.")
        return
    _subscribed_chats.add(message.chat.id)
    _save_subscribers()
    logger.info("Chat %s subscribed", message.chat.id)
    await message.answer("✅ Вы подписались на часовой дайджест (8:00–23:00 МСК).")


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    _load_subscribers()
    if message.chat.id not in _subscribed_chats:
        await message.answer("ℹ️ Вы не подписаны на рассылку.")
        return
    _subscribed_chats.discard(message.chat.id)
    _save_subscribers()
    logger.info("Chat %s unsubscribed", message.chat.id)
    await message.answer("🔕 Вы отписались от рассылки дайджеста.")
