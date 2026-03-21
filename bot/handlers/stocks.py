import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import stocks_service

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("stocks"))
async def cmd_stocks(message: Message):
    try:
        text = await stocks_service.get_stocks()
        await message.answer(text)
    except Exception as e:
        logger.error("Error in /stocks handler: %s", e)
        await message.answer("⚠️ Произошла ошибка при получении котировок. Попробуйте позже.")
