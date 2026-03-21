import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import rates_service

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("rates"))
async def cmd_rates(message: Message):
    try:
        text = await rates_service.get_rates()
        await message.answer(text)
    except Exception as e:
        logger.error("Error in /rates handler: %s", e)
        await message.answer("⚠️ Произошла ошибка при получении курсов валют. Попробуйте позже.")
