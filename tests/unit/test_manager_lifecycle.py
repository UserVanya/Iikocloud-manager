"""Unit tests for IikoCloudApiClientManager Multitone lifecycle."""

import hashlib

import pytest

from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.mixins._base import ApiCredentials
from tests.unit.conftest import credentials, limits

pytestmark = pytest.mark.unit


async def test_same_credentials_same_instance() -> None:
    """Same credentials.key_id returns the same manager instance."""
    creds = credentials()
    method_limits = limits()

    manager1 = await IikoCloudApiClientManager.get_instance(creds, method_limits)
    manager2 = await IikoCloudApiClientManager.get_instance(creds, method_limits)

    assert manager1 is manager2


async def test_close_all_allows_new_instance() -> None:
    """close_all clears the registry so a new instance can be created."""
    creds = credentials()
    method_limits = limits()

    manager1 = await IikoCloudApiClientManager.get_instance(creds, method_limits)
    await IikoCloudApiClientManager.close_all()
    manager2 = await IikoCloudApiClientManager.get_instance(creds, method_limits)

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
