"""Интеграционные тесты авторизации и конкурентности (write-секция).

Проверяют: некорректные credentials, один токен на параллельных
get_organizations, refresh после принудительного 401.

Запуск:
    uv run pytest tests/integration/session -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio

import pytest

from iikocloud import (
    ApiCredentials,
    IikoCloudApiClientManager,
    IikoCloudAuthException,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,  # write-секция config.test.yml
    pytest.mark.asyncio(loop_scope="session"),
]


class TestInvalidCredentials:
    """Некорректные учётные данные → IikoCloudAuthException."""

    async def test_invalid_credentials_raises_auth_exception(self) -> None:
        """Некорректный api_key выбрасывает IikoCloudAuthException на первом вызове."""
        await IikoCloudApiClientManager.close_all()

        credentials = ApiCredentials(
            api_key="invalid-api-key-that-does-not-exist-12345",
            app_id="00000000-0000-0000-0000-000000000001",
            client_secret="invalid-client-secret",
        )
        manager = await IikoCloudApiClientManager.get_instance(credentials)

        try:
            with pytest.raises(IikoCloudAuthException):
                await manager.get_organizations()
        finally:
            await IikoCloudApiClientManager.close_all()


class TestParallelGetOrganizationsShareToken:
    """Параллельные get_organizations делят один токен."""

    async def test_parallel_get_organizations_share_one_token(
        self, fresh_manager: IikoCloudApiClientManager
    ) -> None:
        """Несколько одновременных get_organizations — одна авторизация."""
        results = await asyncio.gather(
            fresh_manager.get_organizations(),
            fresh_manager.get_organizations(),
            fresh_manager.get_organizations(),
            return_exceptions=True,
        )

        for i, result in enumerate(results):
            assert not isinstance(result, BaseException), f"Request {i} failed: {result}"
            assert result is not None
            assert len(result.organizations) > 0

        token_manager = fresh_manager._token_manager
        assert token_manager is not None
        # Холодный старт: ensure_token под lock → ровно одна auth (version == 1)
        assert token_manager.token_version == 1


class TestForced401Refresh:
    """Принудительный 401 → refresh и успешный повтор."""

    async def test_request_after_access_token_invalidation_succeeds(
        self, fresh_manager: IikoCloudApiClientManager
    ) -> None:
        """После порчи access_token запрос проходит через refresh."""
        response1 = await fresh_manager.get_organizations()
        assert response1 is not None
        assert len(response1.organizations) > 0

        token_manager = fresh_manager._token_manager
        assert token_manager is not None
        token_version_before = token_manager.token_version
        token_before = token_manager._token

        # Пауза, чтобы не упереться в auth rate limit на refresh
        await asyncio.sleep(2)

        # Симулируем истечение: следующий API-вызов получит 401
        fresh_manager._api_client.configuration.access_token = "invalid-token-12345"

        response2 = await fresh_manager.get_organizations()

        assert response2 is not None
        assert len(response2.organizations) > 0

        token_version_after = token_manager.token_version
        assert token_version_after > token_version_before
        assert token_manager._token != token_before
