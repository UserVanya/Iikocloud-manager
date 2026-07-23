"""Shared helpers and fixtures for unit tests.

All unit tests build a real ``IikoCloudApiClientManager`` with a stubbed
``TokenManager`` and a stubbed domain API client, so the wiring
(``execute_with_retry`` → rate limits → SDK call) is exercised for real
while nothing touches the network.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest

from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.config_reader import MethodRateLimitsSettings
from iikocloud.mixins._base import ApiCredentials, MethodRateLimits
from iikocloud.rate_limiter import GlobalRateLimiter
from iikocloud.token_manager import TokenManager

# Valid UUID required by GetAccessTokenV2Request.appId
APP_ID = "00000000-0000-0000-0000-000000000001"


def credentials(
    api_key: str = "test-api-key",
    app_id: str = APP_ID,
    client_secret: str = "test-client-secret",
) -> ApiCredentials:
    """Build v2 ApiCredentials for unit tests."""
    return ApiCredentials(
        api_key=api_key,
        app_id=app_id,
        client_secret=client_secret,
    )


def limits() -> MethodRateLimits:
    """Default MethodRateLimits from settings defaults."""
    return MethodRateLimits.from_settings(MethodRateLimitsSettings())


@pytest.fixture(autouse=True)
async def cleanup_singletons() -> AsyncGenerator[None, None]:
    """Reset Multitone registries around every unit test."""
    await IikoCloudApiClientManager.close_all()
    yield
    await IikoCloudApiClientManager.close_all()
    GlobalRateLimiter.reset_instance()
    await TokenManager.close_all()


async def manager_with_stub_token() -> tuple[IikoCloudApiClientManager, MagicMock]:
    """Real manager with TokenManager stubbed (skips auth / ensure)."""
    manager = await IikoCloudApiClientManager.get_instance(credentials(), limits())

    stub_token_manager = MagicMock()
    stub_token_manager.token_version = 1
    manager._token_manager = stub_token_manager
    return manager, stub_token_manager


async def manager_with_stub_api(
    api_attribute: str,
) -> tuple[IikoCloudApiClientManager, MagicMock]:
    """Manager with a stubbed TokenManager and one stubbed lazy API client.

    Args:
        api_attribute: Name of the cached SDK client slot to stub,
            e.g. ``"_customers_api"``.
    """
    manager, _ = await manager_with_stub_token()

    stub_api = MagicMock()
    setattr(manager, api_attribute, stub_api)
    return manager, stub_api
