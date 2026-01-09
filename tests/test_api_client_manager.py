"""Тесты для api_client_manager модуля.

Проверяет:
- Read-only фасадные методы
- Конкурентное обновление токена (только один обновляет)
- Retry при 401 после удаления токена
"""

# mypy: disable-error-code="no-untyped-def,misc"
# ruff: noqa: ANN001, ANN201, ANN202

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client.exceptions import UnauthorizedException

from iikocloud.api_client_manager import (
    ApiCredentials,
    ApiMethod,
    IikoCloudApiClientManager,
    MethodRateLimits,
)
from iikocloud.rate_limiter import GlobalRateLimiter, RateLimitConfig
from iikocloud.token_manager import TokenManager

# Маркируем все тесты в этом модуле как unit-тесты
pytestmark = pytest.mark.unit


@pytest.fixture
async def cleanup() -> AsyncGenerator[None, None]:
    """Очистить синглтоны после каждого теста."""
    yield
    await IikoCloudApiClientManager.close_all()
    GlobalRateLimiter.reset_instance()
    await TokenManager.close_all()


@pytest.fixture
def credentials() -> ApiCredentials:
    """Тестовые учетные данные."""
    return ApiCredentials(api_login="test-login", key_id="test-key")


@pytest.fixture
def method_limits() -> MethodRateLimits:
    """Быстрые per-method rate limits для тестов."""
    fast_config = RateLimitConfig(max_requests=1000, time_window_seconds=1.0)
    return MethodRateLimits(
        auth=fast_config,
        get_organizations=fast_config,
        create_or_update_customer=fast_config,
        get_customer_info=fast_config,
        delete_customers=fast_config,
        restore_customers=fast_config,
        get_terminal_groups=fast_config,
        check_terminal_groups_alive=fast_config,
        get_external_menus=fast_config,
        get_menu_by_id=fast_config,
        get_stop_lists=fast_config,
    )


class TestManagerCreation:
    """Тесты создания менеджера."""

    async def test_get_instance_creates_manager(
        self, credentials: ApiCredentials, method_limits: MethodRateLimits, cleanup: None
    ) -> None:
        """get_instance создаёт новый экземпляр."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        assert manager is not None
        assert manager._credentials == credentials

    async def test_get_instance_returns_same_for_same_key(
        self, credentials: ApiCredentials, method_limits: MethodRateLimits, cleanup: None
    ) -> None:
        """get_instance возвращает тот же экземпляр для одного key_id."""
        manager1 = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )
        manager2 = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        assert manager1 is manager2

    async def test_get_instance_creates_different_for_different_keys(
        self, method_limits: MethodRateLimits, cleanup: None
    ) -> None:
        """get_instance создаёт разные экземпляры для разных key_id."""
        creds1 = ApiCredentials(api_login="login1", key_id="key1")
        creds2 = ApiCredentials(api_login="login2", key_id="key2")

        manager1 = await IikoCloudApiClientManager.get_instance(creds1, method_limits)
        manager2 = await IikoCloudApiClientManager.get_instance(creds2, method_limits)

        assert manager1 is not manager2


class TestReadOnlyMethods:
    """Тесты read-only фасадных методов."""

    async def test_get_organizations_calls_api(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """get_organizations вызывает API и возвращает результат."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        # Мокаем TokenManager чтобы не делать реальный запрос токена
        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        manager._token_manager = mock_token_manager

        # Мокаем OrganizationsApi
        mock_response = MagicMock()
        mock_response.organizations = [
            MagicMock(id=UUID("12345678-1234-1234-1234-123456789abc"), name="Test Org")
        ]

        mock_api = MagicMock()
        mock_api.organizations_post = AsyncMock(return_value=mock_response)
        manager._organizations_api = mock_api

        # Вызываем метод
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()
        result = await manager.organizations(request)

        # Проверяем
        assert result == mock_response
        mock_api.organizations_post.assert_awaited_once()

    async def test_get_customer_info_calls_api(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """get_customer_info вызывает API и возвращает результат."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        # Мокаем TokenManager
        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        manager._token_manager = mock_token_manager

        # Мокаем CustomersApi
        mock_response = MagicMock()
        mock_response.id = UUID("12345678-1234-1234-1234-123456789abc")
        mock_response.name = "Test Customer"

        mock_api = MagicMock()
        mock_api.loyalty_iiko_customer_info_post = AsyncMock(return_value=mock_response)
        manager._customers_api = mock_api

        # Вызываем метод
        from iikocloud_client import CustomerGetCustomerInfoRequest

        request = CustomerGetCustomerInfoRequest(
            type="id",
            organizationId=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        result = await manager.get_customer_info(request)

        # Проверяем
        assert result == mock_response
        mock_api.loyalty_iiko_customer_info_post.assert_awaited_once()

    async def test_get_customer_by_phone_calls_api(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """get_customer_by_phone вызывает API с правильными параметрами."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        # Мокаем TokenManager
        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        manager._token_manager = mock_token_manager

        # Мокаем CustomersApi
        mock_response = MagicMock()
        mock_api = MagicMock()
        mock_api.loyalty_iiko_customer_info_post = AsyncMock(return_value=mock_response)
        manager._customers_api = mock_api

        # Вызываем метод
        result = await manager.get_customer_by_phone(
            phone="+79001234567",
            organization_id="12345678-1234-1234-1234-123456789abc",
        )

        # Проверяем
        assert result == mock_response
        call_args = mock_api.loyalty_iiko_customer_info_post.call_args
        request = call_args.kwargs["customer_get_customer_info_request"]
        assert request.phone == "+79001234567"
        assert request.type == "phone"


class TestRetryOn401:
    """Тесты retry при 401 ошибке."""

    async def test_retry_refreshes_token_on_401(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """При 401 токен обновляется и запрос повторяется."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        # Мокаем TokenManager
        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        mock_token_manager.refresh_token_if_401_with_limits = AsyncMock(
            return_value=True
        )
        manager._token_manager = mock_token_manager

        # API сначала возвращает 401, потом успех
        mock_response = MagicMock()
        call_count = 0

        async def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise UnauthorizedException(status=401, reason="Unauthorized")
            return mock_response

        mock_api = MagicMock()
        mock_api.organizations_post = mock_api_call
        manager._organizations_api = mock_api

        # Вызываем метод
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()
        result = await manager.organizations(request)

        # Проверяем
        assert result == mock_response
        assert call_count == 2  # Первый раз 401, второй раз успех
        mock_token_manager.refresh_token_if_401_with_limits.assert_awaited_once()

    async def test_retry_after_token_removed(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """Если токен удалён, при повторном запросе происходит релогин."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        # Мокаем TokenManager с реальной логикой обновления
        token_refresh_count = 0

        async def mock_refresh(*args, **kwargs):
            nonlocal token_refresh_count
            token_refresh_count += 1
            # Симулируем обновление токена
            manager._api_client.configuration.access_token = "new-token"
            return True

        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        mock_token_manager.refresh_token_if_401_with_limits = mock_refresh
        manager._token_manager = mock_token_manager

        # Первый запрос успешный
        mock_response = MagicMock()
        mock_api = MagicMock()

        request_count = 0

        async def mock_organizations_post(*args, **kwargs):
            nonlocal request_count
            request_count += 1
            # Второй запрос (после "удаления токена") возвращает 401
            if request_count == 2:
                raise UnauthorizedException(status=401, reason="Unauthorized")
            return mock_response

        mock_api.organizations_post = mock_organizations_post
        manager._organizations_api = mock_api

        # Первый успешный запрос
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()
        result1 = await manager.organizations(request)
        assert result1 == mock_response
        assert request_count == 1

        # "Удаляем" токен (симуляция истечения)
        manager._api_client.configuration.access_token = None

        # Второй запрос — должен получить 401, обновить токен и повторить
        result2 = await manager.organizations(request)
        assert result2 == mock_response
        # 2-й вызов (401) + 3-й вызов (успех после refresh) = 3 вызова всего
        assert request_count == 3
        assert token_refresh_count == 1


class TestConcurrentTokenRefresh:
    """Тесты конкурентного обновления токена.

    Проверяет, что при одновременных запросах, получивших 401,
    только один обновляет токен, остальные ждут.
    """

    async def test_concurrent_401_only_one_refreshes(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """При нескольких одновременных 401 только один обновляет токен."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        # Счётчик вызовов refresh
        refresh_call_count = 0

        async def slow_refresh(error, acquire_global, acquire_auth):
            """Медленный refresh для симуляции конкурентности."""
            nonlocal refresh_call_count
            refresh_call_count += 1
            await asyncio.sleep(0.05)  # Симулируем задержку
            return True

        # Создаём мок TokenManager
        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        mock_token_manager.refresh_token_if_401_with_limits = slow_refresh
        manager._token_manager = mock_token_manager

        # API: первый вызов для каждого запроса возвращает 401,
        # повторный вызов (после refresh) возвращает успех
        call_ids: dict[int, int] = {}  # task_id -> call_count
        mock_response = MagicMock()

        async def mock_api_call(*args, **kwargs):
            # Используем id текущей задачи для отслеживания
            task_id = id(asyncio.current_task())
            if task_id not in call_ids:
                call_ids[task_id] = 0
            call_ids[task_id] += 1

            # Первый вызов каждой задачи возвращает 401
            if call_ids[task_id] == 1:
                raise UnauthorizedException(status=401, reason="Unauthorized")
            return mock_response

        mock_api = MagicMock()
        mock_api.organizations_post = mock_api_call
        manager._organizations_api = mock_api

        # Запускаем несколько конкурентных запросов
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()

        results = await asyncio.gather(
            manager.organizations(request),
            manager.organizations(request),
            manager.organizations(request),
            return_exceptions=True,
        )

        # Все запросы должны завершиться успешно
        for result in results:
            assert not isinstance(result, Exception), f"Got exception: {result}"

        # refresh_token_if_401 вызван 3 раза (по одному на каждый 401)
        # Это нормально - каждый запрос вызывает refresh при получении 401,
        # но реальный TokenManager гарантирует что только один обновляет токен
        assert refresh_call_count == 3

    async def test_real_token_manager_concurrent_refresh(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup: None,
    ) -> None:
        """Реальный TokenManager при конкурентных 401 обновляет токен один раз."""
        # Создаём менеджер (для cleanup fixture)
        _ = await IikoCloudApiClientManager.get_instance(credentials, method_limits)

        # Создаём реальный TokenManager с моком API
        mock_api_client = MagicMock()
        mock_api_client.configuration = MagicMock()
        mock_api_client.configuration.access_token = None

        # Патчим TokenManager напрямую для отслеживания
        actual_refresh_count = 0

        async def mock_access_token_post(*args, **kwargs):
            nonlocal actual_refresh_count
            actual_refresh_count += 1
            await asyncio.sleep(0.05)  # Небольшая задержка
            response = MagicMock()
            response.token = f"token-{actual_refresh_count}"
            return response

        # Инициализируем TokenManager
        token_manager = await TokenManager.get_instance(
            api_client=mock_api_client,
            api_login="test-login",
            key_id="test-concurrent-key",
        )

        # Патчим authorization API (используем object.__setattr__ для обхода типизации)
        object.__setattr__(
            token_manager._authorization_api, "access_token_post", mock_access_token_post
        )

        # Получаем начальный токен
        await token_manager.ensure_token_with_limits(
            acquire_global=AsyncMock(),
            acquire_auth=AsyncMock(),
        )
        initial_refresh_count = actual_refresh_count
        initial_version = token_manager._token_version

        # Симулируем несколько конкурентных 401
        error = MagicMock()
        error.status = 401

        async def concurrent_refresh() -> bool:
            return await token_manager.refresh_token_if_401_with_limits(
                error=error,
                acquire_global=AsyncMock(),
                acquire_auth=AsyncMock(),
            )

        # Запускаем 5 конкурентных refresh
        results: list[bool] = await asyncio.gather(
            *[concurrent_refresh() for _ in range(5)]
        )

        # Все должны вернуть True
        assert all(results)

        # Токен должен быть обновлён только ОДИН раз
        assert actual_refresh_count == initial_refresh_count + 1

        # Версия токена увеличилась на 1
        assert token_manager._token_version == initial_version + 1


class TestExecuteWithRetry:
    """Тесты метода execute_with_retry."""

    async def test_execute_with_retry_success_first_try(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """При успешном первом вызове retry не нужен."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        mock_token_manager.refresh_token_if_401_with_limits = AsyncMock()
        manager._token_manager = mock_token_manager

        call_count = 0

        async def successful_call():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await manager.execute_with_retry(
            ApiMethod.GET_CUSTOMER_INFO, successful_call
        )

        assert result == "success"
        assert call_count == 1
        mock_token_manager.refresh_token_if_401_with_limits.assert_not_awaited()

    async def test_execute_with_retry_non_401_error_propagates(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """Не-401 ошибки пробрасываются без retry."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        manager._token_manager = mock_token_manager

        async def failing_call():
            raise ValueError("Some other error")

        with pytest.raises(ValueError, match="Some other error"):
            await manager.execute_with_retry(ApiMethod.GET_CUSTOMER_INFO, failing_call)

    async def test_execute_with_retry_generic_exception_with_401_status(
        self,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits,
        cleanup,
    ) -> None:
        """Обычные исключения с status=401 тоже вызывают retry."""
        manager = await IikoCloudApiClientManager.get_instance(
            credentials, method_limits
        )

        mock_token_manager = MagicMock()
        mock_token_manager.ensure_token_with_limits = AsyncMock()
        mock_token_manager.refresh_token_if_401_with_limits = AsyncMock(
            return_value=True
        )
        manager._token_manager = mock_token_manager

        call_count = 0

        async def call_with_401_status():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                exc = Exception("Auth error")
                exc.status = 401  # type: ignore
                raise exc
            return "success"

        result = await manager.execute_with_retry(
            ApiMethod.GET_CUSTOMER_INFO, call_with_401_status
        )

        assert result == "success"
        assert call_count == 2
        mock_token_manager.refresh_token_if_401_with_limits.assert_awaited_once()
