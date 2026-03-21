from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import rates_service

router = Router()


@router.message(Command("rates"))
async def cmd_rates(message: Message):
    text = await rates_service.get_rates()
    await message.answer(text, parse_mode="Markdown")
