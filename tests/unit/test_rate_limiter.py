"""Тесты для rate_limiter модуля."""

import asyncio
from time import monotonic

import pytest

from iikocloud.rate_limiter import (
    GlobalRateLimiter,
    RateLimitConfig,
    TokenBucketRateLimiter,
)

# Маркируем все тесты в этом модуле как unit-тесты
pytestmark = pytest.mark.unit


class TestRateLimitConfig:
    """Тесты для RateLimitConfig."""

    def test_create_config(self) -> None:
        """Конфигурация создаётся с корректными значениями."""
        config = RateLimitConfig(max_requests=10, time_window_seconds=1.0)

        assert config.max_requests == 10
        assert config.time_window_seconds == 1.0

    def test_config_is_frozen(self) -> None:
        """Конфигурация неизменяема (frozen dataclass)."""
        config = RateLimitConfig(max_requests=10, time_window_seconds=1.0)

        with pytest.raises(AttributeError):
            config.max_requests = 20  # type: ignore[misc]


class TestTokenBucketRateLimiter:
    """Тесты для TokenBucketRateLimiter."""

    async def test_acquire_within_limit(self) -> None:
        """Запросы в пределах лимита выполняются мгновенно."""
        config = RateLimitConfig(max_requests=5, time_window_seconds=1.0)
        limiter = TokenBucketRateLimiter(config)

        start = monotonic()
        for _ in range(5):
            await limiter.acquire()
        elapsed = monotonic() - start

        # Все 5 запросов должны быть мгновенными
        assert elapsed < 0.1

    async def test_acquire_blocks_when_exhausted(self) -> None:
        """При исчерпании токенов acquire блокирует."""
        config = RateLimitConfig(max_requests=1, time_window_seconds=0.2)
        limiter = TokenBucketRateLimiter(config)

        # Первый запрос мгновенный
        await limiter.acquire()

        # Второй запрос должен подождать
        start = monotonic()
        await limiter.acquire()
        elapsed = monotonic() - start

        # Должен был подождать примерно 0.2 секунды
        assert elapsed >= 0.15

    async def test_concurrent_acquires(self) -> None:
        """Конкурентные запросы корректно обрабатываются."""
        config = RateLimitConfig(max_requests=3, time_window_seconds=0.5)
        limiter = TokenBucketRateLimiter(config)

        async def worker() -> float:
            await limiter.acquire()
            return monotonic()

        # Запускаем 5 конкурентных запросов
        start = monotonic()
        results = await asyncio.gather(*[worker() for _ in range(5)])
        total_elapsed = max(results) - start

        # Первые 3 мгновенные, 2 ждут пополнения
        assert total_elapsed >= 0.15  # Хотя бы небольшое ожидание для 4-5 запросов


class TestGlobalRateLimiter:
    """Тесты для GlobalRateLimiter."""

    async def test_get_instance_creates_singleton(self) -> None:
        """get_instance создаёт singleton."""
        GlobalRateLimiter.reset_instance()

        config = RateLimitConfig(max_requests=10, time_window_seconds=1.0)
        instance1 = await GlobalRateLimiter.get_instance(config)
        instance2 = await GlobalRateLimiter.get_instance()

        assert instance1 is instance2

        GlobalRateLimiter.reset_instance()

    async def test_get_instance_requires_config_first_time(self) -> None:
        """Первый вызов get_instance требует config."""
        GlobalRateLimiter.reset_instance()

        with pytest.raises(ValueError, match="config обязателен"):
            await GlobalRateLimiter.get_instance()

    async def test_reset_instance(self) -> None:
        """reset_instance сбрасывает singleton."""
        config = RateLimitConfig(max_requests=10, time_window_seconds=1.0)
        instance1 = await GlobalRateLimiter.get_instance(config)

        GlobalRateLimiter.reset_instance()

        instance2 = await GlobalRateLimiter.get_instance(config)

        assert instance1 is not instance2

        GlobalRateLimiter.reset_instance()

    async def test_acquire(self) -> None:
        """acquire работает через внутренний лимитер."""
        GlobalRateLimiter.reset_instance()

        config = RateLimitConfig(max_requests=2, time_window_seconds=1.0)
        limiter = await GlobalRateLimiter.get_instance(config)

        # Два запроса должны быть мгновенными
        start = monotonic()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = monotonic() - start

        assert elapsed < 0.1

        GlobalRateLimiter.reset_instance()

