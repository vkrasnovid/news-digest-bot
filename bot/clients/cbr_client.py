import logging

from bot.config import CBR_URL
from bot.clients import get_session

logger = logging.getLogger(__name__)


async def fetch_rates() -> dict | None:
    """Fetch currency rates from CBR API. Returns Valute dict or None on failure."""
    try:
        session = await get_session()
        async with session.get(CBR_URL) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
            return data.get("Valute")
    except Exception as e:
        logger.error("CBR API error: %s", e)
        return None
