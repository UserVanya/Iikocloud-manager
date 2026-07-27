"""Общие хелперы для invoice_processing integration-тестов."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from iikocloud_client.exceptions import ApiException

_MAX_429_RETRIES = 3
_429_BACKOFF_SEC = 5.0


async def call_with_429_retry[T](call: Callable[[], Awaitable[T]]) -> T:
    """Вызвать API-метод с retry при 429.

    Стенд жёстко лимитирует invoice endpoints (429 при повторном вызове
    в пределах пары секунд), менеджер ретраит только 401.
    """
    for attempt in range(_MAX_429_RETRIES + 1):
        try:
            return await call()
        except ApiException as exc:
            if exc.status != 429 or attempt == _MAX_429_RETRIES:
                raise
            await asyncio.sleep(_429_BACKOFF_SEC)
    raise AssertionError("unreachable")
