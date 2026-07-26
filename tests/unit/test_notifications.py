"""Unit tests for Notifications domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CorrelationIdResponse,
    OrderAttentionNotificationRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_notifications_api"


async def test_send_notification_delegates() -> None:
    """send_notification проксирует CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.send_notification = AsyncMock(return_value=mock_response)

    request = OrderAttentionNotificationRequest(
        message_type="order_attention",
        organization_id=ORG_ID,
        order_id=ORG_ID,
        order_source="api",
        additional_info="i",
    )
    result = await manager.send_notification(request)

    assert result is mock_response
    mock_api.send_notification.assert_awaited_once_with(
        send_notification_request=request
    )
