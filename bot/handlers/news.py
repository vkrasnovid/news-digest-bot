from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import news_service

router = Router()


@router.message(Command("news"))
async def cmd_news(message: Message):
    text = await news_service.get_all_news()
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
