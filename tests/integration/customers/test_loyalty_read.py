"""Интеграционные read-тесты лояльности Customers API.

Запуск:
    uv run pytest tests/integration/customers/test_loyalty_read.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    CounterMetric,
    CounterPeriod,
    GetCountersRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestGetLoyaltyCounters:
    """get_loyalty_counters против реального API."""

    async def test_counters_for_unknown_guest_returns_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Запрос по несуществующему guest -> валидный ответ со списком counters."""
        response = await manager.get_loyalty_counters(
            GetCountersRequest(
                organization_id=organization_id,
                guest_ids=[UUID("00000000-0000-0000-0000-000000000001")],
                metrics=[CounterMetric.ORDERSCOUNT],
                periods=[CounterPeriod.WEEK],
            )
        )

        assert response is not None
        assert response.counters is not None
