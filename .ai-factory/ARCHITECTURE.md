# Architecture: Layered Architecture

## Overview

The News Digest Bot follows a **Layered Architecture** pattern — a straightforward separation of concerns into horizontal layers: presentation (Telegram bot handlers), business logic (formatting and aggregation), data access (API clients and RSS parsers), and scheduling.

This pattern was chosen because the bot has a simple, linear data flow: fetch data from external APIs → format into readable messages → send via Telegram. There is no complex domain logic, no database, no multi-user state management. Layered Architecture provides clean separation without the overhead of more complex patterns.

## Decision Rationale

- **Project type:** Single-purpose Telegram bot (data aggregation + delivery)
- **Tech stack:** Python 3.11+, aiogram 3.x, aiohttp, APScheduler
- **Team size:** 1 developer, 1 target user
- **Key factor:** Linear data flow with no business logic complexity — simpler is better

## Folder Structure

```
news-digest-bot/
├── bot/
│   ├── __init__.py
│   ├── __main__.py              # Entry point: create bot, register handlers, start scheduler
│   ├── config.py                # Settings from env vars (BOT_TOKEN, CHAT_ID, etc.)
│   ├── handlers/                # Presentation layer — Telegram command handlers
│   │   ├── __init__.py
│   │   ├── start.py             # /start, /help
│   │   ├── rates.py             # /rates
│   │   ├── stocks.py            # /stocks
│   │   ├── news.py              # /news
│   │   ├── digest.py            # /digest
│   │   └── subscription.py      # /subscribe, /unsubscribe
│   ├── services/                # Business logic layer — data aggregation and formatting
│   │   ├── __init__.py
│   │   ├── rates_service.py     # Fetch + format currency rates
│   │   ├── stocks_service.py    # Fetch + format MOEX stocks
│   │   ├── news_service.py      # Fetch + format news from RSS
│   │   └── digest_service.py    # Aggregate all blocks into digest
│   ├── clients/                 # Data access layer — external API clients
│   │   ├── __init__.py
│   │   ├── cbr_client.py        # CBR XML daily API (currency rates)
│   │   ├── moex_client.py       # MOEX ISS API (stock quotes)
│   │   └── rss_client.py        # RSS feed parser (news)
│   ├── scheduler/               # Scheduling layer
│   │   ├── __init__.py
│   │   └── jobs.py              # Hourly digest job (8:00–23:00 MSK)
│   └── utils/                   # Cross-cutting utilities
│       ├── __init__.py
│       └── formatting.py        # Number formatting, emoji helpers
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Module Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    Telegram (aiogram)                     │
└──────────────┬───────────────────────────┬───────────────┘
               │                           │
               ▼                           ▼
┌──────────────────────────┐  ┌────────────────────────────┐
│   handlers/              │  │   scheduler/               │
│   /start /help /rates    │  │   Hourly digest job        │
│   /stocks /news /digest  │  │   (8:00–23:00 MSK)        │
│   /subscribe /unsubscribe│  │                            │
└──────────┬───────────────┘  └──────────┬─────────────────┘
           │                             │
           ▼                             ▼
┌──────────────────────────────────────────────────────────┐
│                    services/                             │
│   rates_service  │  stocks_service  │  news_service     │
│                  │                  │                    │
│                  digest_service (aggregates all three)   │
└──────────┬───────────┬──────────────┬───────────────────┘
           │           │              │
           ▼           ▼              ▼
┌──────────────┐ ┌───────────┐ ┌──────────────┐
│ cbr_client   │ │moex_client│ │ rss_client   │
│ (aiohttp)    │ │ (aiohttp) │ │ (feedparser) │
└──────┬───────┘ └─────┬─────┘ └──────┬───────┘
       │               │              │
       ▼               ▼              ▼
┌──────────────┐ ┌───────────┐ ┌──────────────┐
│cbr-xml-daily │ │iss.moex   │ │Yandex/RBC/   │
│   .ru API    │ │  .com API │ │Regional RSS  │
└──────────────┘ └───────────┘ └──────────────┘
```

## Data Flow

### On-demand (user command)

```
User sends /rates
  → handlers/rates.py receives update
    → calls rates_service.get_rates()
      → calls cbr_client.fetch_rates()
        → HTTP GET https://www.cbr-xml-daily.ru/daily_json.js
      ← returns raw JSON
    ← formats into message block with emoji
  ← sends formatted message to chat
```

### Scheduled digest (every hour)

```
APScheduler triggers at HH:00 (8–23 MSK)
  → scheduler/jobs.py calls digest_service.build_digest()
    → concurrently fetches:
      ├── rates_service.get_rates()
      ├── stocks_service.get_stocks()
      └── news_service.get_news()
    ← returns 3 formatted message blocks
  → sends 3 separate messages to CHAT_ID
```

## Dependency Rules

- **handlers/** → **services/** → **clients/** (strict top-down)
- **scheduler/** → **services/** (same level as handlers, calls services directly)
- **utils/** ← any layer (cross-cutting, no upward dependencies)
- **config.py** ← any layer (read-only settings)

Allowed:
- ✅ handlers import from services
- ✅ services import from clients
- ✅ scheduler imports from services
- ✅ any layer imports from utils and config

Forbidden:
- ❌ clients must NOT import from services or handlers
- ❌ services must NOT import from handlers
- ❌ handlers must NOT import directly from clients (go through services)

## External APIs

### CBR Currency Rates
- **URL:** `https://www.cbr-xml-daily.ru/daily_json.js`
- **Method:** GET, no auth
- **Response:** JSON with `Valute.USD`, `Valute.EUR`, `Valute.CNY` objects
- **Fields:** `Value` (current rate), `Previous` (yesterday's rate)
- **Rate limit:** None documented, poll no more than once per minute

### MOEX ISS Stocks
- **URL:** `https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?securities=BELU,SBER,ROSN,SIBN,PHOR`
- **Method:** GET, no auth
- **Response:** JSON with `marketdata.data` array
- **Fields:** SECID (ticker), LAST (price), CHANGE (absolute), LASTTOPREVPRICE (% change)
- **Rate limit:** None for public data, reasonable polling

### News RSS Feeds
- **World news:** `https://news.yandex.ru/world.rss`
- **Russia trending:** `https://news.yandex.ru/index.rss`
- **Saratov local:** `https://news.yandex.ru/Saratov/index.rss` (+ regional sources as backup)
- **Format:** Standard RSS/XML, parse with `feedparser`

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Runtime | Python 3.11+ | Main language |
| Bot framework | aiogram 3.x | Async Telegram Bot API |
| HTTP client | aiohttp | Async HTTP for API calls |
| RSS parser | feedparser | Parse RSS/Atom feeds |
| Scheduler | APScheduler | Cron-like job scheduling |
| Timezone | pytz / zoneinfo | MSK timezone handling |
| Config | python-dotenv | Load .env variables |
| Deploy | Docker + docker-compose | Container deployment |

## Key Principles

1. **All I/O is async** — use `aiohttp` for HTTP calls, `aiogram` for Telegram. Never block the event loop.
2. **Graceful degradation** — if any API is down, send what's available with an error note for the failed section. Never crash the entire digest.
3. **Concurrent fetching** — use `asyncio.gather()` to fetch rates, stocks, and news in parallel for the digest.
4. **Single source of config** — all settings (token, chat_id, tickers, feed URLs) come from `config.py` via environment variables.
5. **Stateless design** — no database. Subscription state is minimal (single user, hardcoded chat_id). If needed later, add SQLite.

## Code Examples

### Client layer — fetching currency rates
```python
# bot/clients/cbr_client.py
import aiohttp
import logging

logger = logging.getLogger(__name__)

CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

async def fetch_rates() -> dict | None:
    """Fetch currency rates from CBR API. Returns None on failure."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CBR_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                return data["Valute"]
    except Exception as e:
        logger.error("CBR API error: %s", e)
        return None
```

### Service layer — formatting rates
```python
# bot/services/rates_service.py
from bot.clients import cbr_client

CURRENCIES = ["USD", "EUR", "CNY"]

async def get_rates() -> str:
    """Fetch and format currency rates block."""
    valutes = await cbr_client.fetch_rates()
    if valutes is None:
        return "💱 *Курсы валют*\n⚠️ Данные временно недоступны"

    lines = ["💱 *Курсы валют ЦБ РФ*\n"]
    for code in CURRENCIES:
        v = valutes.get(code)
        if not v:
            continue
        current = v["Value"]
        previous = v["Previous"]
        diff = current - previous
        arrow = "🔺" if diff > 0 else "🔻" if diff < 0 else "▪️"
        lines.append(f"{arrow} {code}/RUB: {current:.2f} ({diff:+.2f})")

    return "\n".join(lines)
```

### Handler layer — command handler
```python
# bot/handlers/rates.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from bot.services import rates_service

router = Router()

@router.message(Command("rates"))
async def cmd_rates(message: Message):
    text = await rates_service.get_rates()
    await message.answer(text, parse_mode="Markdown")
```

### Digest service — aggregating all blocks
```python
# bot/services/digest_service.py
import asyncio
from bot.services import rates_service, stocks_service, news_service

async def build_digest() -> list[str]:
    """Build 3 message blocks for the full digest."""
    rates, stocks, news = await asyncio.gather(
        rates_service.get_rates(),
        stocks_service.get_stocks(),
        news_service.get_news(),
        return_exceptions=True,
    )

    messages = []

    # Block 1: Currencies + Stocks
    block1_parts = []
    block1_parts.append(rates if isinstance(rates, str) else "💱 Курсы валют: ⚠️ ошибка")
    block1_parts.append(stocks if isinstance(stocks, str) else "📊 Акции: ⚠️ ошибка")
    messages.append("\n\n".join(block1_parts))

    # Block 2: World + Russia news
    # Block 3: Saratov news
    if isinstance(news, tuple):
        world_russia, saratov = news
        messages.append(world_russia)
        messages.append(saratov)
    else:
        messages.append("📰 Новости: ⚠️ ошибка загрузки")

    return messages
```

### Scheduler — hourly digest job
```python
# bot/scheduler/jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.services import digest_service
from bot.config import CHAT_ID

def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def send_digest():
        messages = await digest_service.build_digest()
        for msg in messages:
            await bot.send_message(CHAT_ID, msg, parse_mode="Markdown")

    scheduler.add_job(
        send_digest,
        CronTrigger(hour="8-23", minute=0, timezone="Europe/Moscow"),
    )
    return scheduler
```

## Error Handling Strategy

```
API call fails
  → client returns None
    → service returns fallback message ("⚠️ Данные временно недоступны")
      → handler/scheduler sends whatever is available
        → user sees partial digest instead of nothing
```

- Each client has its own `try/except` with logging
- Services check for `None` returns and substitute fallback text
- `asyncio.gather(return_exceptions=True)` prevents one failure from blocking others
- No retry logic in v1 — if an API is down, the next hourly run will try again

## Anti-Patterns

- ❌ **Don't call APIs from handlers directly** — always go through services for formatting and error handling
- ❌ **Don't use synchronous HTTP** (`requests`) — everything must be async to avoid blocking the bot
- ❌ **Don't store state in global variables** — use config for constants, pass dependencies explicitly
- ❌ **Don't catch and silence exceptions** — always log errors before returning fallback values
- ❌ **Don't hardcode feed URLs or tickers in services** — keep them in config.py for easy changes
