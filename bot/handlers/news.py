import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import news_service
from bot.utils.formatting import split_message

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("news"))
async def cmd_news(message: Message):
    try:
        text = await news_service.get_all_news()
        for part in split_message(text):
            await message.answer(part, disable_web_page_preview=True)
    except Exception as e:
        logger.error("Error in /news handler: %s", e)
        await message.answer("⚠️ Произошла ошибка при получении новостей. Попробуйте позже.")
