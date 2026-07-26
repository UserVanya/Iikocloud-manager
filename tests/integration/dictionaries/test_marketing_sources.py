"""Интеграционный read-тест MarketingSources API (read-секция).

Запуск:
    uv run pytest tests/integration/dictionaries/test_marketing_sources.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import MarketingSourcesRequest

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestGetMarketingSources:
    async def test_get_marketing_sources_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_marketing_sources(
            MarketingSourcesRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.marketing_sources is not None
        if response.marketing_sources:
            source = response.marketing_sources[0]
            assert source.id is not None
            assert isinstance(source.name, str)
            assert source.organization_id is not None
