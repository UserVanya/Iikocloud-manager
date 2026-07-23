"""Unit tests for Terminal Groups domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    TerminalGroupsIsAliveRequest,
    TerminalGroupsIsAliveResponse,
    TerminalGroupsRequest,
    TerminalGroupsResponse,
)

from iikocloud.mixins._base import ApiMethod
from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")


async def test_get_terminal_groups_calls_api_with_request() -> None:
    """get_terminal_groups delegates to SDK with the given request."""
    manager, mock_api = await manager_with_stub_api("_terminal_groups_api")

    mock_response = MagicMock(spec=TerminalGroupsResponse)
    mock_api.get_terminal_groups = AsyncMock(return_value=mock_response)

    request = TerminalGroupsRequest(organization_ids=[ORG_ID])
    result = await manager.get_terminal_groups(request)

    assert result is mock_response
    mock_api.get_terminal_groups.assert_awaited_once_with(
        terminal_groups_request=request
    )


async def test_check_terminal_groups_availability_calls_api_with_request() -> None:
    """check_terminal_groups_availability delegates to SDK with the given request."""
    manager, mock_api = await manager_with_stub_api("_terminal_groups_api")

    mock_response = MagicMock(spec=TerminalGroupsIsAliveResponse)
    mock_api.check_terminal_groups_availability = AsyncMock(
        return_value=mock_response
    )

    group_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    request = TerminalGroupsIsAliveRequest(
        organization_ids=[ORG_ID],
        terminal_group_ids=[group_id],
    )
    result = await manager.check_terminal_groups_availability(request)

    assert result is mock_response
    mock_api.check_terminal_groups_availability.assert_awaited_once_with(
        terminal_groups_is_alive_request=request
    )


async def test_get_terminal_groups_by_organization_builds_request() -> None:
    """get_terminal_groups_by_organization builds TerminalGroupsRequest."""
    manager, mock_api = await manager_with_stub_api("_terminal_groups_api")

    mock_response = MagicMock(spec=TerminalGroupsResponse)
    mock_api.get_terminal_groups = AsyncMock(return_value=mock_response)

    result = await manager.get_terminal_groups_by_organization(ORG_ID)

    assert result is mock_response
    mock_api.get_terminal_groups.assert_awaited_once()
    call_kwargs = mock_api.get_terminal_groups.await_args.kwargs
    request = call_kwargs["terminal_groups_request"]
    assert isinstance(request, TerminalGroupsRequest)
    assert request.organization_ids == [ORG_ID]


async def test_get_terminal_groups_by_organization_accepts_str_id() -> None:
    """get_terminal_groups_by_organization converts string organization_id."""
    manager, mock_api = await manager_with_stub_api("_terminal_groups_api")

    mock_api.get_terminal_groups = AsyncMock(return_value=MagicMock())

    await manager.get_terminal_groups_by_organization(str(ORG_ID))

    call_kwargs = mock_api.get_terminal_groups.await_args.kwargs
    request = call_kwargs["terminal_groups_request"]
    assert request.organization_ids == [ORG_ID]


async def test_get_terminal_groups_uses_execute_with_retry() -> None:
    """get_terminal_groups routes through execute_with_retry."""
    manager, mock_api = await manager_with_stub_api("_terminal_groups_api")
    mock_api.get_terminal_groups = AsyncMock(return_value=MagicMock())

    async def _passthrough(method, api_call):  # noqa: ANN001
        return await api_call()

    manager.execute_with_retry = AsyncMock(side_effect=_passthrough)

    await manager.get_terminal_groups(
        TerminalGroupsRequest(organization_ids=[ORG_ID])
    )

    manager.execute_with_retry.assert_awaited_once()
    method_arg = manager.execute_with_retry.await_args.args[0]
    assert method_arg is ApiMethod.GET_TERMINAL_GROUPS
