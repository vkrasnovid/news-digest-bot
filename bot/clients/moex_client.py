import logging

from bot.config import MOEX_STOCKS_URL, MOEX_GOLD_URL, TICKERS
from bot.clients import get_session

logger = logging.getLogger(__name__)


async def fetch_stocks() -> list[dict] | None:
    """Fetch stock quotes from MOEX ISS. Returns list of dicts or None on failure."""
    # BUG-012: Use securities.columns and iss.only for efficient server-side filtering
    params = {
        "iss.meta": "off",
        "iss.only": "marketdata",
        "marketdata.columns": "SECID,LAST,CHANGE,LASTTOPREVPRICE",
    }
    try:
        session = await get_session()
        async with session.get(MOEX_STOCKS_URL, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

            marketdata = data.get("marketdata", {})
            columns = marketdata.get("columns", [])
            rows = marketdata.get("data", [])

            results = []
            for row in rows:
                item = dict(zip(columns, row))
                if item.get("SECID") in TICKERS and item.get("LAST") is not None:
                    results.append(item)
            return results if results else None
    except Exception as e:
        logger.error("MOEX stocks API error: %s", e)
        return None


async def fetch_gold() -> dict | None:
    """Fetch XAU/RUB from MOEX currency market. Returns dict with price info or None."""
    params = {
        "iss.meta": "off",
        "iss.only": "marketdata",
        "marketdata.columns": "SECID,LAST,CHANGE",
    }
    try:
        session = await get_session()
        async with session.get(MOEX_GOLD_URL, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

            marketdata = data.get("marketdata", {})
            columns = marketdata.get("columns", [])
            rows = marketdata.get("data", [])

            for row in rows:
                item = dict(zip(columns, row))
                if item.get("SECID") == "GLDRUB_TOM" and item.get("LAST") is not None:
                    return item
            return None
    except Exception as e:
        logger.error("MOEX gold API error: %s", e)
        return None
