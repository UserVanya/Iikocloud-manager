"""Unit tests for TokenManager (auth v2)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from iikocloud_client.exceptions import UnauthorizedException

from iikocloud.exceptions import IikoCloudAuthException
from iikocloud.token_manager import TokenManager

pytestmark = pytest.mark.unit

# Valid UUID required by GetAccessTokenV2Request.appId
APP_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def mock_api_client() -> MagicMock:
    """Create a mock ApiClient with configuration.access_token."""
    client = MagicMock()
    client.configuration = MagicMock()
    client.configuration.access_token = None
    return client


@pytest.fixture
async def token_manager(mock_api_client: MagicMock) -> TokenManager:
    """Create a TokenManager instance with v2 credentials."""
    await TokenManager.close_all()

    manager = await TokenManager.get_instance(
        api_client=mock_api_client,
        api_key="test-api-key",
        app_id=APP_ID,
        client_secret="test-client-secret",
        key_id="test-key",
    )
    yield manager

    await TokenManager.close_all()


class TestTokenManagerCreation:
    """get_instance multitone behavior."""

    async def test_get_instance_returns_same_for_same_key(
        self, mock_api_client: MagicMock
    ) -> None:
        """Same key_id returns the same TokenManager instance."""
        await TokenManager.close_all()

        manager1 = await TokenManager.get_instance(
            mock_api_client,
            api_key="k",
            app_id=APP_ID,
            client_secret="s",
            key_id="key1",
        )
        manager2 = await TokenManager.get_instance(
            mock_api_client,
            api_key="k",
            app_id=APP_ID,
            client_secret="s",
            key_id="key1",
        )

        assert manager1 is manager2
        await TokenManager.close_all()

    async def test_get_instance_creates_different_for_different_keys(
        self, mock_api_client: MagicMock
    ) -> None:
        """Different key_id values get different TokenManager instances."""
        await TokenManager.close_all()

        manager1 = await TokenManager.get_instance(
            mock_api_client,
            api_key="k",
            app_id=APP_ID,
            client_secret="s",
            key_id="key1",
        )
        manager2 = await TokenManager.get_instance(
            mock_api_client,
            api_key="k",
            app_id=APP_ID,
            client_secret="s",
            key_id="key2",
        )

        assert manager1 is not manager2
        await TokenManager.close_all()


class TestEnsureToken:
    """ensure_token_with_limits behavior."""

    async def test_fetches_token_once_when_none(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Fetches via authenticate_v2 when no token is cached."""
        mock_response = MagicMock()
        mock_response.token = "new-token"

        with patch.object(
            token_manager._authorization_api,
            "authenticate_v2",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_auth:
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            await token_manager.ensure_token_with_limits(
                acquire_global, acquire_auth
            )

            assert mock_api_client.configuration.access_token == "new-token"
            assert token_manager.token_version == 1
            mock_auth.assert_awaited_once()
            acquire_global.assert_awaited_once()
            acquire_auth.assert_awaited_once()

    async def test_skips_fetch_when_token_exists(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Does not call auth API when a token is already present."""
        token_manager._token = "existing-token"
        mock_api_client.configuration.access_token = "existing-token"

        acquire_global = AsyncMock()
        acquire_auth = AsyncMock()

        with patch.object(
            token_manager._authorization_api,
            "authenticate_v2",
            new_callable=AsyncMock,
        ) as mock_auth:
            await token_manager.ensure_token_with_limits(
                acquire_global, acquire_auth
            )
            mock_auth.assert_not_awaited()

        acquire_global.assert_not_awaited()
        acquire_auth.assert_not_awaited()

    async def test_concurrent_ensure_fetches_once(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Concurrent ensure_token_with_limits calls fetch the token once."""
        call_count = 0

        async def slow_auth(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            response = MagicMock()
            response.token = "shared-token"
            return response

        with patch.object(
            token_manager._authorization_api,
            "authenticate_v2",
            side_effect=slow_auth,
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            await asyncio.gather(
                token_manager.ensure_token_with_limits(
                    acquire_global, acquire_auth
                ),
                token_manager.ensure_token_with_limits(
                    acquire_global, acquire_auth
                ),
                token_manager.ensure_token_with_limits(
                    acquire_global, acquire_auth
                ),
            )

        assert call_count == 1
        assert mock_api_client.configuration.access_token == "shared-token"
        assert token_manager.token_version == 1

    async def test_401_on_auth_raises_auth_exception(
        self, token_manager: TokenManager
    ) -> None:
        """401 from authenticate_v2 becomes IikoCloudAuthException."""
        with patch.object(
            token_manager._authorization_api,
            "authenticate_v2",
            new_callable=AsyncMock,
            side_effect=UnauthorizedException(status=401, reason="Unauthorized"),
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            with pytest.raises(IikoCloudAuthException):
                await token_manager.ensure_token_with_limits(
                    acquire_global, acquire_auth
                )


class TestRefreshToken:
    """refresh_token_if_401 with version-based dedup."""

    async def test_returns_false_for_non_401(
        self, token_manager: TokenManager
    ) -> None:
        """Non-401 errors do not trigger a refresh."""
        acquire_global = AsyncMock()
        acquire_auth = AsyncMock()

        result = await token_manager.refresh_token_if_401(
            Exception("Some error"), acquire_global, acquire_auth
        )

        assert result is False
        acquire_global.assert_not_awaited()

    async def test_refreshes_on_401(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Refreshes token and bumps token_version on 401."""
        token_manager._token = "old-token"
        token_manager._token_version = 1

        mock_response = MagicMock()
        mock_response.token = "refreshed-token"

        with patch.object(
            token_manager._authorization_api,
            "authenticate_v2",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()
            error = MagicMock()
            error.status = 401

            result = await token_manager.refresh_token_if_401(
                error, acquire_global, acquire_auth, version_before=1
            )

            assert result is True
            assert token_manager._token == "refreshed-token"
            assert token_manager.token_version == 2
            assert mock_api_client.configuration.access_token == "refreshed-token"

    async def test_dedup_skips_fetch_when_version_already_bumped(
        self, token_manager: TokenManager
    ) -> None:
        """If version_before is stale, skip another authenticate_v2 call."""
        token_manager._token = "already-new"
        token_manager._token_version = 2

        with patch.object(
            token_manager._authorization_api,
            "authenticate_v2",
            new_callable=AsyncMock,
        ) as mock_auth:
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()
            error = MagicMock()
            error.status = 401

            result = await token_manager.refresh_token_if_401(
                error, acquire_global, acquire_auth, version_before=1
            )

            assert result is True
            mock_auth.assert_not_awaited()
            acquire_global.assert_not_awaited()

    async def test_concurrent_refresh_dedup_with_version(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Concurrent 401 refreshes call authenticate_v2 only once."""
        token_manager._token = "old-token"
        token_manager._token_version = 1
        call_count = 0

        async def slow_auth(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            response = MagicMock()
            response.token = "new-token"
            return response

        error = MagicMock()
        error.status = 401

        with patch.object(
            token_manager._authorization_api,
            "authenticate_v2",
            side_effect=slow_auth,
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            results = await asyncio.gather(
                token_manager.refresh_token_if_401(
                    error, acquire_global, acquire_auth, version_before=1
                ),
                token_manager.refresh_token_if_401(
                    error, acquire_global, acquire_auth, version_before=1
                ),
            )

        assert all(results)
        assert call_count == 1
        assert token_manager.token_version == 2
        assert mock_api_client.configuration.access_token == "new-token"


class TestCloseAll:
    """close_all clears the multitone registry."""

    async def test_clears_instances(self, mock_api_client: MagicMock) -> None:
        """close_all empties _instances."""
        await TokenManager.close_all()

        await TokenManager.get_instance(
            mock_api_client,
            api_key="k",
            app_id=APP_ID,
            client_secret="s",
            key_id="key1",
        )
        await TokenManager.get_instance(
            mock_api_client,
            api_key="k",
            app_id=APP_ID,
            client_secret="s",
            key_id="key2",
        )

        assert len(TokenManager._instances) == 2

        await TokenManager.close_all()

        assert len(TokenManager._instances) == 0
