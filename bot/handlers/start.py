from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

WELCOME_TEXT = (
    "👋 *Привет!*\n\n"
    "Я — бот новостного дайджеста. Каждый час (с 8:00 до 23:00 МСК) "
    "присылаю сводку:\n"
    "💱 Курсы валют и золото\n"
    "📊 Котировки акций MOEX\n"
    "📰 Топ новости мира, России и Саратова\n\n"
    "Используй /help для списка команд."
)

HELP_TEXT = (
    "📋 *Команды*\n\n"
    "/start — Приветствие\n"
    "/help — Список команд\n"
    "/rates — Курсы валют + золото\n"
    "/stocks — Котировки акций MOEX\n"
    "/news — Новости\n"
    "/digest — Полная сводка сейчас\n"
    "/subscribe — Подписаться на рассылку\n"
    "/unsubscribe — Отписаться от рассылки"
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(WELCOME_TEXT, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode="Markdown")
