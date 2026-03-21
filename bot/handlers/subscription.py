import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()
logger = logging.getLogger(__name__)

# Simple in-memory subscription state (single-user bot)
_subscribed_chats: set[int] = set()
_initialized: bool = False


def _ensure_default(chat_id: int) -> None:
    """Initialize default subscriber on first access."""
    global _initialized
    if not _initialized:
        from bot.config import CHAT_ID
        _subscribed_chats.add(CHAT_ID)
        _initialized = True


def is_subscribed(chat_id: int) -> bool:
    _ensure_default(chat_id)
    return chat_id in _subscribed_chats


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message):
    _ensure_default(message.chat.id)
    if message.chat.id in _subscribed_chats:
        await message.answer("✅ Вы уже подписаны на рассылку дайджеста.")
        return
    _subscribed_chats.add(message.chat.id)
    logger.info("Chat %s subscribed", message.chat.id)
    await message.answer("✅ Вы подписались на часовой дайджест (8:00–23:00 МСК).")


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message):
    _ensure_default(message.chat.id)
    if message.chat.id not in _subscribed_chats:
        await message.answer("ℹ️ Вы не подписаны на рассылку.")
        return
    _subscribed_chats.discard(message.chat.id)
    logger.info("Chat %s unsubscribed", message.chat.id)
    await message.answer("🔕 Вы отписались от рассылки дайджеста.")
