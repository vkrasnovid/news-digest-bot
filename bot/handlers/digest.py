import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import digest_service
from bot.utils.formatting import split_message

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("digest"))
async def cmd_digest(message: Message):
    try:
        messages = await digest_service.build_digest()
        for msg in messages:
            for part in split_message(msg):
                await message.answer(part, disable_web_page_preview=True)
    except Exception as e:
        logger.error("Error in /digest handler: %s", e)
        await message.answer("⚠️ Произошла ошибка при формировании дайджеста. Попробуйте позже.")
