import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services.details_service import get_details

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("details"))
async def cmd_details(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer("Укажи тему: /details Конфликт в Иране")
        return

    topic = args[1].strip()
    try:
        text = await get_details(topic)
        await message.answer(text, disable_web_page_preview=True)
    except Exception:
        logger.exception("Error fetching details for topic: %s", topic)
        await message.answer("Не удалось получить новости. Попробуй позже.")
