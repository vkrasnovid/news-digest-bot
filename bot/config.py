import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
CHAT_ID: int = int(os.getenv("CHAT_ID", "210706056"))

# Currency pairs to display
CURRENCIES: list[str] = ["USD", "EUR", "CNY"]

# MOEX stock tickers
TICKERS: list[str] = ["BELU", "SBER", "ROSN", "SIBN", "PHOR"]

# Ticker display names
TICKER_NAMES: dict[str, str] = {
    "BELU": "Белуга",
    "SBER": "Сбер",
    "ROSN": "Роснефть",
    "SIBN": "Газпром нефть",
    "PHOR": "ФосАгро",
}

# External API URLs
CBR_URL: str = "https://www.cbr-xml-daily.ru/daily_json.js"
MOEX_STOCKS_URL: str = (
    "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json"
)
MOEX_GOLD_URL: str = (
    "https://iss.moex.com/iss/engines/currency/markets/selt/boards/CETS/securities.json"
)

# RSS feed URLs
RSS_WORLD: str = "https://news.yandex.ru/world.rss"
RSS_RUSSIA: str = "https://news.yandex.ru/index.rss"
RSS_SARATOV: str = "https://news.yandex.ru/Saratov/index.rss"

# Scheduler settings
DIGEST_HOURS: str = "8-23"  # MSK hours for hourly digest
DIGEST_MINUTE: int = 0
TIMEZONE: str = "Europe/Moscow"

# HTTP timeout in seconds
HTTP_TIMEOUT: int = 10
