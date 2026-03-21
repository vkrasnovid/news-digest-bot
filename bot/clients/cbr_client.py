import aiohttp
import logging

from bot.config import CBR_URL, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


async def fetch_rates() -> dict | None:
    """Fetch currency rates from CBR API. Returns Valute dict or None on failure."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                CBR_URL, timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
                return data.get("Valute")
    except Exception as e:
        logger.error("CBR API error: %s", e)
        return None
