import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# BUG-007: Validate CHAT_ID on startup
_chat_id_raw = os.getenv("CHAT_ID", "").strip()
if not _chat_id_raw:
    raise RuntimeError("CHAT_ID environment variable is required")
try:
    CHAT_ID: int = int(_chat_id_raw)
except ValueError:
    raise RuntimeError(f"CHAT_ID must be an integer, got: {_chat_id_raw!r}")

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
RSS_WORLD: str = "https://ria.ru/export/rss2/archive/index.xml"
RSS_RUSSIA: str = "https://lenta.ru/rss"
RSS_RUSSIA_2: str = "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"
RSS_SARATOV: str = "https://saratov.mk.ru/rss/"
RSS_SARATOV_2: str = "https://nversia.ru/rss/"

# Scheduler settings
DIGEST_HOURS: str = "8-23"  # MSK hours for hourly digest
DIGEST_MINUTE: int = 0
TIMEZONE: str = "Europe/Moscow"

# HTTP timeout in seconds
HTTP_TIMEOUT: int = 10

# Subscribers persistence file
SUBSCRIBERS_FILE: str = os.getenv("SUBSCRIBERS_FILE", "subscribers.json")
