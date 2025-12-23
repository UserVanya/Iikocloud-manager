"""Тесты для token_manager модуля."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from iikocloud.exceptions import IikoCloudAuthException
from iikocloud.token_manager import TokenManager

# Маркируем все тесты в этом модуле как unit-тесты
pytestmark = pytest.mark.unit


@pytest.fixture
def mock_api_client() -> MagicMock:
    """Создать мок ApiClient."""
    client = MagicMock()
    client.configuration = MagicMock()
    client.configuration.access_token = None
    return client


@pytest.fixture
async def token_manager(mock_api_client: MagicMock) -> TokenManager:
    """Создать экземпляр TokenManager для тестов."""
    # Сбрасываем состояние
    await TokenManager.close_all()

    manager = await TokenManager.get_instance(
        api_client=mock_api_client,
        api_login="test-login",
        key_id="test-key",
    )
    yield manager

    # Очистка
    await TokenManager.close_all()


class TestTokenManagerCreation:
    """Тесты создания TokenManager."""

    async def test_get_instance_returns_singleton_for_same_key(
        self, mock_api_client: MagicMock
    ) -> None:
        """get_instance возвращает тот же экземпляр для одного key_id."""
        await TokenManager.close_all()

        manager1 = await TokenManager.get_instance(
            mock_api_client, "login", "key1"
        )
        manager2 = await TokenManager.get_instance(
            mock_api_client, "login", "key1"
        )

        assert manager1 is manager2

        await TokenManager.close_all()

    async def test_get_instance_creates_different_for_different_keys(
        self, mock_api_client: MagicMock
    ) -> None:
        """get_instance создаёт разные экземпляры для разных key_id."""
        await TokenManager.close_all()

        manager1 = await TokenManager.get_instance(
            mock_api_client, "login", "key1"
        )
        manager2 = await TokenManager.get_instance(
            mock_api_client, "login", "key2"
        )

        assert manager1 is not manager2

        await TokenManager.close_all()


class TestEnsureToken:
    """Тесты ensure_token_with_limits."""

    async def test_fetches_token_when_none(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Получает токен, если его нет."""
        mock_response = MagicMock()
        mock_response.token = "new-token"

        with patch.object(
            token_manager._authorization_api,
            "access_token_post",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            await token_manager.ensure_token_with_limits(
                acquire_global, acquire_auth
            )

            assert mock_api_client.configuration.access_token == "new-token"
            acquire_global.assert_awaited_once()
            acquire_auth.assert_awaited_once()

    async def test_skips_fetch_when_token_exists(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Пропускает получение, если токен уже есть."""
        token_manager._token = "existing-token"
        mock_api_client.configuration.access_token = "existing-token"

        acquire_global = AsyncMock()
        acquire_auth = AsyncMock()

        await token_manager.ensure_token_with_limits(acquire_global, acquire_auth)

        # Не должен был вызывать acquire
        acquire_global.assert_not_awaited()
        acquire_auth.assert_not_awaited()

    async def test_raises_on_api_error(
        self, token_manager: TokenManager
    ) -> None:
        """Выбрасывает IikoCloudAuthException при ошибке API."""
        with patch.object(
            token_manager._authorization_api,
            "access_token_post",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            with pytest.raises(IikoCloudAuthException, match="API Error"):
                await token_manager.ensure_token_with_limits(
                    acquire_global, acquire_auth
                )


class TestRefreshToken:
    """Тесты refresh_token_if_401_with_limits."""

    async def test_returns_false_for_non_401(
        self, token_manager: TokenManager
    ) -> None:
        """Возвращает False для не-401 ошибок."""
        error = Exception("Some error")

        acquire_global = AsyncMock()
        acquire_auth = AsyncMock()

        result = await token_manager.refresh_token_if_401_with_limits(
            error, acquire_global, acquire_auth
        )

        assert result is False
        acquire_global.assert_not_awaited()

    async def test_refreshes_on_401(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Обновляет токен при 401 ошибке."""
        token_manager._token = "old-token"
        token_manager._token_version = 1

        error = MagicMock()
        error.status = 401

        mock_response = MagicMock()
        mock_response.token = "refreshed-token"

        with patch.object(
            token_manager._authorization_api,
            "access_token_post",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            result = await token_manager.refresh_token_if_401_with_limits(
                error, acquire_global, acquire_auth
            )

            assert result is True
            assert token_manager._token == "refreshed-token"
            assert token_manager._token_version == 2
            assert mock_api_client.configuration.access_token == "refreshed-token"

    async def test_concurrent_refresh_waits(
        self, token_manager: TokenManager, mock_api_client: MagicMock
    ) -> None:
        """Конкурентные обновления ждут завершения первого."""
        token_manager._token = "old-token"
        token_manager._token_version = 1

        call_count = 0

        async def slow_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            response = MagicMock()
            response.token = "new-token"
            return response

        error = MagicMock()
        error.status = 401

        with patch.object(
            token_manager._authorization_api,
            "access_token_post",
            side_effect=slow_post,
        ):
            acquire_global = AsyncMock()
            acquire_auth = AsyncMock()

            # Запускаем несколько конкурентных обновлений
            results = await asyncio.gather(
                token_manager.refresh_token_if_401_with_limits(
                    error, acquire_global, acquire_auth
                ),
                token_manager.refresh_token_if_401_with_limits(
                    error, acquire_global, acquire_auth
                ),
            )

            # Оба должны вернуть True
            assert all(results)
            # Но API должен быть вызван только один раз
            assert call_count == 1


class TestCloseAll:
    """Тесты close_all."""

    async def test_clears_instances(self, mock_api_client: MagicMock) -> None:
        """close_all очищает все экземпляры."""
        await TokenManager.close_all()

        await TokenManager.get_instance(mock_api_client, "login", "key1")
        await TokenManager.get_instance(mock_api_client, "login", "key2")

        assert len(TokenManager._instances) == 2

        await TokenManager.close_all()

        assert len(TokenManager._instances) == 0

