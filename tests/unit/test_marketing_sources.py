"""Unit tests for MarketingSources domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import MarketingSourcesRequest, MarketingSourcesResponse

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_marketing_sources_api"


async def test_get_marketing_sources_delegates() -> None:
    """get_marketing_sources проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=MarketingSourcesResponse)
    mock_api.get_marketing_sources = AsyncMock(return_value=mock_response)

    request = MarketingSourcesRequest(organization_ids=[ORG_ID])
    result = await manager.get_marketing_sources(request)

    assert result is mock_response
    mock_api.get_marketing_sources.assert_awaited_once_with(
        marketing_sources_request=request
    )
