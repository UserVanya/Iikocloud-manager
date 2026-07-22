"""Unit tests for IikoCloudApiClientManager Multitone lifecycle."""

import hashlib

import pytest

from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.mixins._base import ApiCredentials, MethodRateLimits
from iikocloud.config_reader import MethodRateLimitsSettings
from iikocloud.rate_limiter import GlobalRateLimiter
from iikocloud.token_manager import TokenManager

pytestmark = pytest.mark.unit


def _credentials(
    api_key: str = "test-api-key",
    app_id: str = "00000000-0000-0000-0000-000000000001",
    client_secret: str = "test-client-secret",
) -> ApiCredentials:
    """Build v2 ApiCredentials for lifecycle tests."""
    return ApiCredentials(
        api_key=api_key,
        app_id=app_id,
        client_secret=client_secret,
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


async def test_same_credentials_same_instance() -> None:
    """Same credentials.key_id returns the same manager instance."""
    creds = _credentials()
    limits = _limits()

    manager1 = await IikoCloudApiClientManager.get_instance(creds, limits)
    manager2 = await IikoCloudApiClientManager.get_instance(creds, limits)

    assert manager1 is manager2


async def test_close_all_allows_new_instance() -> None:
    """close_all clears the registry so a new instance can be created."""
    creds = _credentials()
    limits = _limits()

    manager1 = await IikoCloudApiClientManager.get_instance(creds, limits)
    await IikoCloudApiClientManager.close_all()
    manager2 = await IikoCloudApiClientManager.get_instance(creds, limits)

    assert manager1 is not manager2


def test_key_id_is_fingerprint_not_manual() -> None:
    """key_id is a stable fingerprint of api_key:app_id (not a manual field)."""
    creds = ApiCredentials(api_key="a", app_id="b", client_secret="c")

    assert creds.key_id
    assert creds.key_id == ApiCredentials("a", "b", "c").key_id
    expected = hashlib.sha1(b"a:b").hexdigest()[:16]
    assert creds.key_id == expected
    # client_secret must not affect the Multitone key
    assert (
        creds.key_id
        == ApiCredentials(api_key="a", app_id="b", client_secret="other").key_id
    )
