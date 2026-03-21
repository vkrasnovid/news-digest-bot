from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import digest_service

router = Router()


@router.message(Command("digest"))
async def cmd_digest(message: Message):
    messages = await digest_service.build_digest()
    for msg in messages:
        await message.answer(msg, parse_mode="Markdown", disable_web_page_preview=True)
