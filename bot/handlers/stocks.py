from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import stocks_service

router = Router()


@router.message(Command("stocks"))
async def cmd_stocks(message: Message):
    text = await stocks_service.get_stocks()
    await message.answer(text, parse_mode="Markdown")
