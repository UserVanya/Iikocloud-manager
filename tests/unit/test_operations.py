"""Unit tests for Operations domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    ErrorCommandStatus,
    GetCommandStatusRequest,
    InProgressCommandStatus,
    SuccessCommandStatus,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_operations_api"


async def test_get_command_status_delegates() -> None:
    """get_command_status проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=SuccessCommandStatus)
    mock_api.get_command_status = AsyncMock(return_value=mock_response)

    request = GetCommandStatusRequest(
        organization_id=ORG_ID, correlation_id=ORG_ID
    )
    result = await manager.get_command_status(request)

    assert result is mock_response
    mock_api.get_command_status.assert_awaited_once_with(
        get_command_status_request=request
    )


async def test_wait_command_success_immediately() -> None:
    """wait_command: Success с первого опроса."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        return_value=SuccessCommandStatus(state="Success")
    )

    result = await manager.wait_command(ORG_ID, ORG_ID, interval=0.01)

    assert isinstance(result, SuccessCommandStatus)


async def test_wait_command_in_progress_then_success() -> None:
    """wait_command: InProgress -> Success."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        side_effect=[
            InProgressCommandStatus(state="InProgress"),
            SuccessCommandStatus(state="Success"),
        ]
    )

    result = await manager.wait_command(ORG_ID, ORG_ID, interval=0.01)

    assert isinstance(result, SuccessCommandStatus)
    assert mock_api.get_command_status.await_count == 2


async def test_wait_command_error_status_returned() -> None:
    """wait_command: Error-статус возвращается вызывающему."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        return_value=ErrorCommandStatus(state="Error", error_reason="boom")
    )

    result = await manager.wait_command(ORG_ID, ORG_ID, interval=0.01)

    assert isinstance(result, ErrorCommandStatus)
    assert result.error_reason == "boom"


async def test_wait_command_timeout() -> None:
    """wait_command: timeout -> TimeoutError."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.get_command_status = AsyncMock(
        return_value=InProgressCommandStatus(state="InProgress")
    )

    with pytest.raises(TimeoutError, match="wait_command"):
        await manager.wait_command(
            ORG_ID, ORG_ID, timeout=0.05, interval=0.01
        )
