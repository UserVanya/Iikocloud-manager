"""Rate limiting для iikocloud API.

Реализация Token Bucket алгоритма для ограничения частоты запросов.
"""

import asyncio
from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class RateLimitConfig:
    """Конфигурация rate limiter.

    Attributes:
        max_requests: Максимальное количество запросов в окне
        time_window_seconds: Размер временного окна в секундах
    """

    max_requests: int
    time_window_seconds: float


class TokenBucketRateLimiter:
    """Token Bucket rate limiter.

    Позволяет выполнять не более max_requests запросов
    за time_window_seconds секунд.
    """

    def __init__(self, config: RateLimitConfig) -> None:
        """Инициализирует лимитер.

        Args:
            config: Конфигурация rate limiting
        """
        self._max_tokens = config.max_requests
        self._refill_rate = config.max_requests / config.time_window_seconds
        self._tokens = float(config.max_requests)
        self._last_refill = monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Получить токен для выполнения запроса.

        Блокирует выполнение до тех пор, пока токен не станет доступен.
        """
        async with self._lock:
            await self._wait_for_token()
            self._tokens -= 1

    async def _wait_for_token(self) -> None:
        """Ожидать появления токена."""
        while True:
            self._refill()
            if self._tokens >= 1:
                return

            # Вычисляем время ожидания до появления одного токена
            tokens_needed = 1 - self._tokens
            wait_time = tokens_needed / self._refill_rate
            await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        """Пополнить токены пропорционально прошедшему времени."""
        now = monotonic()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self._refill_rate

        self._tokens = min(self._max_tokens, self._tokens + tokens_to_add)
        self._last_refill = now


class GlobalRateLimiter:
    """Singleton для общего лимита всех запросов iikocloud.

    Используется для ограничения общего количества запросов к API,
    независимо от группы API.
    """

    _instance: "GlobalRateLimiter | None" = None
    _lock: asyncio.Lock | None = None

    def __init__(self, config: RateLimitConfig) -> None:
        """Инициализирует глобальный лимитер.

        Args:
            config: Конфигурация rate limiting
        """
        self._limiter = TokenBucketRateLimiter(config)

    @classmethod
    async def get_instance(
        cls, config: RateLimitConfig | None = None
    ) -> "GlobalRateLimiter":
        """Получить singleton-экземпляр.

        Args:
            config: Конфигурация (обязательна при первом вызове)

        Returns:
            Экземпляр GlobalRateLimiter

        Raises:
            ValueError: Если config не передан при первом создании
        """
        # Создаём lock при первом вызове (для корректной работы в разных event loop)
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is None:
                if config is None:
                    raise ValueError(
                        "config обязателен при первом создании GlobalRateLimiter"
                    )
                cls._instance = cls(config)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Сбросить singleton (для тестов)."""
        cls._instance = None
        cls._lock = None

    async def acquire(self) -> None:
        """Получить глобальный токен."""
        await self._limiter.acquire()
