"""Unit tests for Webhooks domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CorrelationIdResponse,
    GetWebHookSettingsRequest,
    GetWebHookSettingsResponse,
    UpdateWebHookSettingsRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_webhooks_api"


async def test_get_webhook_settings_delegates() -> None:
    """get_webhook_settings проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetWebHookSettingsResponse)
    mock_api.get_webhook_settings = AsyncMock(return_value=mock_response)

    request = GetWebHookSettingsRequest(organization_id=ORG_ID)
    result = await manager.get_webhook_settings(request)

    assert result is mock_response
    mock_api.get_webhook_settings.assert_awaited_once_with(
        get_web_hook_settings_request=request
    )


async def test_update_webhook_settings_delegates() -> None:
    """update_webhook_settings проксирует CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.update_webhook_settings = AsyncMock(return_value=mock_response)

    request = UpdateWebHookSettingsRequest(
        organization_id=ORG_ID, web_hooks_uri="https://example.com/hook"
    )
    result = await manager.update_webhook_settings(request)

    assert result is mock_response
    mock_api.update_webhook_settings.assert_awaited_once_with(
        update_web_hook_settings_request=request
    )
