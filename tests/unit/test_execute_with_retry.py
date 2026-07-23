"""Unit tests for ``execute_with_retry`` (rate limits + single 401 retry)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from iikocloud_client.exceptions import UnauthorizedException

from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.config_reader import MethodRateLimitsSettings
from iikocloud.mixins._base import ApiCredentials, ApiMethod, MethodRateLimits
from iikocloud.rate_limiter import GlobalRateLimiter
from iikocloud.token_manager import TokenManager

pytestmark = pytest.mark.unit

APP_ID = "00000000-0000-0000-0000-000000000001"


def _credentials() -> ApiCredentials:
    """Build v2 ApiCredentials for execute_with_retry tests."""
    return ApiCredentials(
        api_key="test-api-key",
        app_id=APP_ID,
        client_secret="test-client-secret",
    )


def _limits() -> MethodRateLimits:
    """Default MethodRateLimits from settings defaults."""
    return MethodRateLimits.from_settings(MethodRateLimitsSettings())


@pytest.fixture(autouse=True)
async def cleanup_singletons() -> None:
    """Reset Multitone registries between tests."""
    await IikoCloudApiClientManager.close_all()
    yield
    await IikoCloudApiClientManager.close_all()
    GlobalRateLimiter.reset_instance()
    await TokenManager.close_all()


async def _manager_with_mock_token() -> tuple[
    IikoCloudApiClientManager, MagicMock
]:
    """Real manager with TokenManager stubbed (skip auth / ensure)."""
    manager = await IikoCloudApiClientManager.get_instance(
        _credentials(), _limits()
    )
    mock_token_manager = MagicMock()
    mock_token_manager.token_version = 1
    mock_token_manager.refresh_token_if_401 = AsyncMock(return_value=False)
    manager._token_manager = mock_token_manager
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
