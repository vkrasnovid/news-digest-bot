import aiohttp

from bot.config import HTTP_TIMEOUT

_session: aiohttp.ClientSession | None = None


async def get_session() -> aiohttp.ClientSession:
    """Return a shared aiohttp.ClientSession, creating one if needed."""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        )
    return _session


async def close_session() -> None:
    """Close the shared session."""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None
