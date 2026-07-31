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
    """key_id is a stable fingerprint of api_key:app_id:client_secret (not a manual field)."""
    creds = ApiCredentials(api_key="a", app_id="b", client_secret="c")

    assert creds.key_id
    assert creds.key_id == ApiCredentials("a", "b", "c").key_id
    expected = hashlib.sha1(b"a:b:c").hexdigest()[:16]
    assert creds.key_id == expected


def test_key_id_differs_when_only_client_secret_differs() -> None:
    """Regression: client_secret must affect the Multitone key.

    Otherwise a caller with the correct api_key/app_id but a wrong or empty
    client_secret would be handed another tenant's cached, already-authenticated
    manager/token instance instead of getting its own.
    """
    creds_a = ApiCredentials(api_key="a", app_id="b", client_secret="right-secret")
    creds_b = ApiCredentials(api_key="a", app_id="b", client_secret="wrong-secret")

    assert creds_a.key_id != creds_b.key_id


def test_key_id_is_16_lowercase_hex_chars() -> None:
    """key_id keeps its 16-hex-character shape — consumers depend on it."""
    key_id = ApiCredentials(api_key="a", app_id="b", client_secret="c").key_id

    assert len(key_id) == 16
    assert key_id == key_id.lower()
    assert all(char in "0123456789abcdef" for char in key_id)
