"""Unit tests for ``execute_with_retry`` (rate limits + single 401 retry)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from iikocloud_client.exceptions import UnauthorizedException

from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.mixins._base import ApiMethod
from tests.unit.conftest import manager_with_stub_token

pytestmark = pytest.mark.unit


async def _manager_with_mock_token() -> tuple[IikoCloudApiClientManager, MagicMock]:
    """Stubbed manager whose refresh_token_if_401 defaults to False."""
    manager, mock_token_manager = await manager_with_stub_token()
    mock_token_manager.refresh_token_if_401 = AsyncMock(return_value=False)
    return manager, mock_token_manager


async def test_success_acquires_global_then_method_limits() -> None:
    """Success path acquires global limiter, then method limiter, then calls API."""
    manager, _tm = await _manager_with_mock_token()
    method = ApiMethod.GET_ORGANIZATIONS
    order: list[str] = []

    manager._global_limiter.acquire = AsyncMock(
        side_effect=lambda: order.append("global")
    )
    method_limiter = MagicMock()
    method_limiter.acquire = AsyncMock(
        side_effect=lambda: order.append("method")
    )
    manager._method_limiters[method] = method_limiter

    api_call = AsyncMock(return_value="ok")
    result = await manager.execute_with_retry(method, api_call)

    assert result == "ok"
    assert order == ["global", "method"]
    api_call.assert_awaited_once()
    manager._global_limiter.acquire.assert_awaited_once()
    method_limiter.acquire.assert_awaited_once()


async def test_401_then_refresh_retries_once_and_returns() -> None:
    """401 + successful refresh → one retry through limits, returns result."""
    manager, mock_tm = await _manager_with_mock_token()
    mock_tm.refresh_token_if_401 = AsyncMock(return_value=True)

    method = ApiMethod.GET_ORGANIZATIONS
    # Track limit acquires: first attempt + retry = 2 global + 2 method
    manager._global_limiter.acquire = AsyncMock()
    method_limiter = MagicMock()
    method_limiter.acquire = AsyncMock()
    manager._method_limiters[method] = method_limiter

    call_count = 0

    async def api_call() -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise UnauthorizedException(status=401, reason="Unauthorized")
        return "after-refresh"

    result = await manager.execute_with_retry(method, api_call)

    assert result == "after-refresh"
    assert call_count == 2
    mock_tm.refresh_token_if_401.assert_awaited_once()
    assert manager._global_limiter.acquire.await_count == 2
    assert method_limiter.acquire.await_count == 2


async def test_token_version_captured_after_rate_limit_wait() -> None:
    """version_before is sampled after the limiter wait, not before it.

    Waiting on a method bucket can take minutes; if another coroutine refreshes
    the token meanwhile, a version captured before the wait would make
    refresh_token_if_401 take the "already refreshed by someone else" shortcut
    and skip the refresh this request actually needs.
    """
    manager, mock_tm = await _manager_with_mock_token()
    method = ApiMethod.GET_ORGANIZATIONS

    async def _bump_version_while_waiting() -> None:
        # Another coroutine refreshed the token while we were throttled.
        mock_tm.token_version = 7

    manager._global_limiter.acquire = AsyncMock()
    method_limiter = MagicMock()
    method_limiter.acquire = AsyncMock(side_effect=_bump_version_while_waiting)
    manager._method_limiters[method] = method_limiter

    api_call = AsyncMock(
        side_effect=UnauthorizedException(status=401, reason="Unauthorized")
    )

    with pytest.raises(UnauthorizedException):
        await manager.execute_with_retry(method, api_call)

    assert mock_tm.refresh_token_if_401.await_args.kwargs["version_before"] == 7


async def test_401_then_refresh_false_reraises_without_retry() -> None:
    """401 + refresh returns False → re-raises; no successful retry call."""
    manager, mock_tm = await _manager_with_mock_token()
    mock_tm.refresh_token_if_401 = AsyncMock(return_value=False)

    method = ApiMethod.GET_ORGANIZATIONS
    manager._global_limiter.acquire = AsyncMock()
    method_limiter = MagicMock()
    method_limiter.acquire = AsyncMock()
    manager._method_limiters[method] = method_limiter

    api_call = AsyncMock(
        side_effect=UnauthorizedException(status=401, reason="Unauthorized")
    )

    with pytest.raises(UnauthorizedException):
        await manager.execute_with_retry(method, api_call)

    api_call.assert_awaited_once()
    mock_tm.refresh_token_if_401.assert_awaited_once()
    # Limits acquired only for the failed attempt (no retry)
    assert manager._global_limiter.acquire.await_count == 1
    assert method_limiter.acquire.await_count == 1
