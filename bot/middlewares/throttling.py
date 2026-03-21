import time
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)

THROTTLE_SECONDS = 2


class ThrottlingMiddleware(BaseMiddleware):
    """Simple per-user rate limiting middleware."""

    def __init__(self, rate_limit: float = THROTTLE_SECONDS) -> None:
        self._rate_limit = rate_limit
        self._last_call: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else event.chat.id
        now = time.monotonic()
        last = self._last_call.get(user_id, 0)
        if now - last < self._rate_limit:
            logger.debug("Throttled user %s", user_id)
            return None
        self._last_call[user_id] = now
        return await handler(event, data)
