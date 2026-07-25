"""Unit tests for DeliveryRestrictions domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    GetAllowedRestrictionsRequest,
    GetAllowedRestrictionsResponse,
    GetDeliveryRestrictionsRequest,
    GetDeliveryRestrictionsResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_delivery_restrictions_api"


async def test_get_allowed_delivery_restrictions_delegates() -> None:
    """get_allowed_delivery_restrictions проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetAllowedRestrictionsResponse)
    mock_api.get_allowed_delivery_restrictions = AsyncMock(
        return_value=mock_response
    )

    request = GetAllowedRestrictionsRequest(
        is_courier_delivery=True, organization_ids=[ORG_ID]
    )
    result = await manager.get_allowed_delivery_restrictions(request)

    assert result is mock_response
    mock_api.get_allowed_delivery_restrictions.assert_awaited_once_with(
        get_allowed_restrictions_request=request
    )


async def test_get_delivery_restrictions_delegates() -> None:
    """get_delivery_restrictions проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetDeliveryRestrictionsResponse)
    mock_api.get_delivery_restrictions = AsyncMock(return_value=mock_response)

    request = GetDeliveryRestrictionsRequest(organization_ids=[ORG_ID])
    result = await manager.get_delivery_restrictions(request)

    assert result is mock_response
    mock_api.get_delivery_restrictions.assert_awaited_once_with(
        get_delivery_restrictions_request=request
    )
