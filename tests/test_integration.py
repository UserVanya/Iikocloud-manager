"""Интеграционные тесты с реальными запросами к iikocloud API.

Эти тесты используют реальный API и требуют:
1. Настроенный config.yml с валидным api_login
2. Переменную окружения IIKOCLOUD_CONFIG

Запуск только интеграционных тестов:
    uv run pytest -m integration -v

Запуск всех тестов кроме интеграционных:
    uv run pytest -m "not integration" -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import random
from uuid import UUID

import pytest

from iikocloud import (
    ApiCredentials,
    IikoCloudApiClientManager,
    IikoCloudAuthException,
)
from tests.conftest import (
    EXISTING_CUSTOMER_PHONE,
    NOT_FOUND_CUSTOMER_PHONE,
    generate_random_phone,
)

# Маркируем весь модуль как интеграционные и медленные тесты
pytestmark = [pytest.mark.integration, pytest.mark.slow]


class TestInvalidApiKey:
    """Тесты с некорректным API ключом."""

    async def test_invalid_api_key_raises_auth_exception(self) -> None:
        """Некорректный API ключ выбрасывает IikoCloudAuthException."""
        # Создаём менеджер с заведомо неверным ключом
        credentials = ApiCredentials(
            api_login="invalid-api-key-that-does-not-exist-12345",
            key_id="test-invalid-key",
        )
        manager = await IikoCloudApiClientManager.get_instance(credentials)

        try:
            # Любой вызов должен попытаться получить токен и получить 401
            with pytest.raises(IikoCloudAuthException) as exc_info:
                await manager.organizations()

            # Проверяем сообщение об ошибке
            assert "Некорректный API-ключ" in str(exc_info.value)
            assert "401" in str(exc_info.value)
        finally:
            # Обязательно очищаем после теста
            await IikoCloudApiClientManager.close_all()


class TestRealApiGetOrganizations:
    """Тесты get_organizations с реальным API."""

    async def test_get_organizations_returns_list(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """get_organizations возвращает список организаций."""
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()
        response = await manager.organizations(request)

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "organizations")
        assert hasattr(response, "correlation_id")
        assert isinstance(response.correlation_id, UUID)

        # Должна быть хотя бы одна организация
        assert len(response.organizations) > 0

        # Проверяем структуру организации
        org = response.organizations[0]
        assert hasattr(org, "id")
        assert hasattr(org, "name")
        assert isinstance(org.id, UUID)
        assert isinstance(org.name, str)
        assert len(org.name) > 0

    async def test_get_organizations_twice_uses_same_token(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """Повторный вызов использует тот же токен (без повторной авторизации)."""
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()

        # Первый запрос
        response1 = await manager.organizations(request)
        token_version_1 = manager._token_manager._token_version  # type: ignore

        # Второй запрос
        response2 = await manager.organizations(request)
        token_version_2 = manager._token_manager._token_version  # type: ignore

        # Оба запроса успешны
        assert response1 is not None
        assert response2 is not None

        # Версия токена не изменилась (не было повторной авторизации)
        assert token_version_1 == token_version_2


class TestRealApiTokenRefresh:
    """Тесты обновления токена при 401."""

    async def test_request_after_token_invalidation_succeeds(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """Запрос после 'инвалидации' токена успешен (происходит refresh).

        Note: Этот тест может периодически падать из-за rate limiting
        на стороне iiko API (502 Bad Gateway). Это не баг нашего кода.
        """
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()

        # Первый успешный запрос
        response1 = await manager.organizations(request)
        assert response1 is not None
        token_version_before = manager._token_manager._token_version  # type: ignore
        token_before = manager._token_manager._token  # type: ignore
        # Пауза чтобы не получить rate limit от iiko
        await asyncio.sleep(2)

        # "Портим" токен (симулируем истечение)
        manager._api_client.configuration.access_token = "invalid-token-12345"

        # Следующий запрос должен получить 401, обновить токен и повторить
        response2 = await manager.organizations(request)

        # Запрос успешен
        assert response2 is not None
        assert len(response2.organizations) > 0

        # Токен был обновлён
        token_version_after = manager._token_manager._token_version  # type: ignore
        assert token_version_after > token_version_before
        token_after = manager._token_manager._token  # type: ignore

        assert token_after != token_before


class TestRealApiConcurrentRequests:
    """Тесты конкурентных запросов к реальному API."""

    async def test_concurrent_requests_all_succeed(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """Несколько одновременных запросов успешно выполняются."""
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()

        # Запускаем 3 конкурентных запроса
        results = await asyncio.gather(
            manager.organizations(request),
            manager.organizations(request),
            manager.organizations(request),
            return_exceptions=True,
        )

        # Все запросы должны быть успешными
        for i, result in enumerate(results):
            assert not isinstance(result, BaseException), f"Request {i} failed: {result}"
            assert result is not None
            assert len(result.organizations) > 0

    async def test_concurrent_requests_after_token_invalidation(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """Конкурентные запросы после инвалидации токена — только один refresh."""
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()

        # Первый запрос для получения токена
        await manager.organizations(request)
        token_version_before = manager._token_manager._token_version  # type: ignore

        # Пауза чтобы не получить rate limit от iiko
        await asyncio.sleep(2)

        # "Портим" токен
        manager._api_client.configuration.access_token = "invalid-token-xyz"

        # Запускаем несколько конкурентных запросов
        # Все получат 401, но только один должен обновить токен
        results = await asyncio.gather(
            manager.organizations(request),
            manager.organizations(request),
            manager.organizations(request),
            return_exceptions=True,
        )

        # Все запросы успешны
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Request {i} failed: {result}"

        # Токен обновлён только ОДИН раз (версия увеличилась на 1)
        token_version_after = manager._token_manager._token_version  # type: ignore
        assert token_version_after == token_version_before + 1


class TestRealApiRateLimiting:
    """Тесты rate limiting на реальном API."""

    async def test_rate_limiting_does_not_cause_errors(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """Rate limiting не вызывает ошибок при последовательных запросах."""
        from iikocloud_client import OrganizationsGetOrganizationsRequest

        request = OrganizationsGetOrganizationsRequest()

        # Делаем 5 последовательных запросов
        for i in range(5):
            response = await manager.organizations(request)
            assert response is not None, f"Request {i} failed"
            assert len(response.organizations) > 0


class TestRealApiCustomerGetByPhone:
    """Тесты get_customer_by_phone с реальным API."""

    async def test_get_existing_customer_by_phone(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение существующего клиента по номеру телефона."""
        response = await manager.get_customer_by_phone(
            phone=EXISTING_CUSTOMER_PHONE,
            organization_id=str(organization_id),
        )

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "id")
        assert hasattr(response, "phone")

        # Телефон должен совпадать (iiko может форматировать номер)
        assert response.phone is not None

    async def test_get_not_found_customer_returns_error(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Запрос несуществующего клиента возвращает ошибку или пустой ответ."""
        from iikocloud_client.exceptions import ApiException

        try:
            response = await manager.get_customer_by_phone(
                phone=NOT_FOUND_CUSTOMER_PHONE,
                organization_id=str(organization_id),
            )
            # Если не выбросило исключение, проверяем что клиент не найден
            # iiko может вернуть пустой ответ или null
            assert response.id is None or response.phone is None
        except ApiException as e:
            # 400 или 404 — ожидаемое поведение для несуществующего клиента
            assert e.status in (400, 404), f"Неожиданный статус: {e.status}"


class TestRealApiCustomerCreateAndManage:
    """Тесты создания и управления клиентами."""

    async def test_create_new_customer(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Создание нового клиента с случайным номером телефона."""
        from iikocloud_client import CustomerCreateOrUpdateCustomerRequest

        random_phone = generate_random_phone()

        request = CustomerCreateOrUpdateCustomerRequest(
            organizationId=organization_id,
            phone=random_phone,
            name="Test Customer",
        )

        response = await manager.create_or_update_customer(request)

        # Проверяем что клиент создан
        assert response is not None
        assert hasattr(response, "id")
        assert response.id is not None

        # Сохраняем ID для последующих тестов
        customer_id = response.id

        # Проверяем что клиент доступен по телефону
        await asyncio.sleep(1)  # Небольшая пауза для синхронизации

        get_response = await manager.get_customer_by_phone(
            phone=random_phone,
            organization_id=str(organization_id),
        )
        assert get_response is not None
        assert get_response.id == customer_id

    async def test_update_existing_customer(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Обновление существующего клиента."""
        from iikocloud_client import CustomerCreateOrUpdateCustomerRequest

        # Сначала получаем существующего клиента
        existing = await manager.get_customer_by_phone(
            phone=EXISTING_CUSTOMER_PHONE,
            organization_id=str(organization_id),
        )
        assert existing is not None
        assert existing.id is not None

        # Обновляем имя
        new_name = f"Updated Test {random.randint(1000, 9999)}"
        request = CustomerCreateOrUpdateCustomerRequest(
            id=existing.id,
            organizationId=organization_id,
            phone=EXISTING_CUSTOMER_PHONE,
            name=new_name,
        )

        response = await manager.create_or_update_customer(request)

        # Проверяем что обновление прошло
        assert response is not None
        assert response.id == existing.id

    async def test_logical_delete_and_restore_customer(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Логическое удаление и восстановление клиента."""
        from iikocloud_client import CustomerCreateOrUpdateCustomerRequest

        # Создаём нового клиента для теста
        random_phone = generate_random_phone()
        create_request = CustomerCreateOrUpdateCustomerRequest(
            organizationId=organization_id,
            phone=random_phone,
            name="Delete Test Customer",
        )
        create_response = await manager.create_or_update_customer(create_request)
        assert create_response.id is not None
        customer_id = create_response.id

        await asyncio.sleep(1)

        # Логически удаляем клиента
        delete_response = await manager.logical_delete_customer(
            customer_id=str(customer_id),
            organization_id=str(organization_id),
        )
        assert delete_response is not None

        await asyncio.sleep(1)

        # Восстанавливаем клиента
        restore_response = await manager.logical_restore_customer(
            customer_id=str(customer_id),
            organization_id=str(organization_id),
        )
        assert restore_response is not None

        await asyncio.sleep(1)

        # Проверяем что клиент снова доступен
        get_response = await manager.get_customer_by_phone(
            phone=random_phone,
            organization_id=str(organization_id),
        )
        assert get_response is not None
        assert get_response.id == customer_id


class TestRealApiTerminalGroups:
    """Тесты Terminal Groups API."""

    async def test_get_terminal_groups_by_organization(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение терминальных групп для организации."""
        response = await manager.get_terminal_groups_by_organization(
            organization_id=str(organization_id),
        )

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "terminal_groups")
        assert hasattr(response, "correlation_id")

    async def test_get_terminal_groups_with_request(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение терминальных групп через полный запрос."""
        from iikocloud_client import TerminalsTerminalGroupsRequest

        request = TerminalsTerminalGroupsRequest(
            organizationIds=[organization_id],
            includeDisabled=True,
        )
        response = await manager.terminal_groups(request)

        assert response is not None
        assert hasattr(response, "terminal_groups")

    async def test_check_terminal_group_alive(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Проверка доступности терминальной группы."""
        # Сначала получаем терминальные группы
        groups_response = await manager.get_terminal_groups_by_organization(
            organization_id=str(organization_id),
        )
        assert groups_response.terminal_groups is not None
        assert len(groups_response.terminal_groups) > 0

        # Берём первую группу с терминалами
        terminal_group = None
        for org_groups in groups_response.terminal_groups:
            if org_groups.items and len(org_groups.items) > 0:
                terminal_group = org_groups.items[0]
                break

        if terminal_group is None:
            pytest.skip("Нет доступных терминальных групп")

        # Проверяем доступность
        response = await manager.check_terminal_group_alive_by_organization(
            terminal_group_id=str(terminal_group.id),
            organization_id=str(organization_id),
        )

        assert response is not None
        assert hasattr(response, "is_alive_status")
        assert hasattr(response, "correlation_id")


class TestRealApiMenu:
    """Тесты Menu API."""

    async def test_get_external_menus(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """Получение списка внешних меню."""
        response = await manager.external_menus()

        assert response is not None
        assert hasattr(response, "correlation_id")
        # Внешние меню могут быть не настроены, поэтому проверяем только структуру
        assert hasattr(response, "external_menus")

    # @pytest.mark.xfail(
    #     reason="iikocloud-client bug: ExternalMenuV3 не полностью определён"
    # )
    async def test_get_menu_by_id_v2(
        self, manager: IikoCloudApiClientManager,
        menu_test_organization_id: UUID,
        menu_id: str,
    ) -> None:
        """Получение меню по ID организации с 'мигуста' в названии."""
        # Запрашиваем меню по ID
        response = await manager.get_menu_by_id_and_organization_v2(
            organization_id=str(menu_test_organization_id),
            external_menu_id=menu_id,
        )

        assert response is not None

    async def test_get_menu_by_id_v3(
        self, manager: IikoCloudApiClientManager,
        menu_test_organization_id: UUID,
        menu_id: str,
    ) -> None:
        """Получение меню по ID организации с 'мигуста' в названии."""
        # Запрашиваем меню по ID
        response = await manager.get_menu_by_id_and_organization_v3(
            organization_id=str(menu_test_organization_id),
            external_menu_id=menu_id,
        )

        assert response is not None

    async def test_get_menu_by_id_v4(
        self, manager: IikoCloudApiClientManager,
        menu_test_organization_id: UUID,
        menu_id: str,
    ) -> None:
        """Получение меню по ID организации с 'мигуста' в названии."""
        # Запрашиваем меню по ID
        response = await manager.get_menu_by_id_and_organization_v4(
            organization_id=str(menu_test_organization_id),
            external_menu_id=menu_id,
        )

        assert response is not None

    async def test_get_stop_lists_by_organization(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение стоп-листов для организации."""
        response = await manager.get_stop_lists_by_organization(
            organization_ids=[str(organization_id)],
        )

        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "terminal_group_stop_lists")

    async def test_get_stop_lists_with_request(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение стоп-листов через полный запрос."""
        from iikocloud_client import StopListsStopListsRequest

        request = StopListsStopListsRequest(
            organizationIds=[organization_id],
        )
        response = await manager.stop_lists(request)

        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "terminal_group_stop_lists")


class TestRealApiDictionaries:
    """Тесты Dictionaries API с реальным API."""

    async def test_get_delivery_cancel_causes(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение причин отмены доставки для организации."""
        response = await manager.get_delivery_cancel_causes_by_organization(
            organization_id=str(organization_id),
        )

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "cancel_causes")
        assert isinstance(response.correlation_id, UUID)

    async def test_get_order_types(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение типов заказов для организации."""
        response = await manager.get_order_types_by_organization(
            organization_id=str(organization_id),
        )

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "order_types")
        assert isinstance(response.correlation_id, UUID)

    async def test_get_payment_types(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение типов платежей для организации."""
        response = await manager.get_payment_types_by_organization(
            organization_id=str(organization_id),
        )

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "payment_types")
        assert isinstance(response.correlation_id, UUID)

    async def test_get_discounts(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение скидок для организации."""
        response = await manager.get_discounts_by_organization(
            organization_id=str(organization_id),
        )

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "discounts")
        assert isinstance(response.correlation_id, UUID)

    async def test_get_removal_types(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение типов удаления для организации."""
        response = await manager.get_removal_types_by_organization(
            organization_id=str(organization_id),
        )

        # Проверяем структуру ответа
        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "removal_types")
        assert isinstance(response.correlation_id, UUID)

    async def test_get_delivery_cancel_causes_with_request(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение причин отмены через полный запрос."""
        from iikocloud_client import CancelCausesCancelCausesRequest

        request = CancelCausesCancelCausesRequest(
            organizationIds=[organization_id],
        )
        response = await manager.delivery_cancel_causes(request)

        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "cancel_causes")

    async def test_get_order_types_with_request(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение типов заказов через полный запрос."""
        from iikocloud_client import OrderTypesOrderTypesRequest

        request = OrderTypesOrderTypesRequest(
            organizationIds=[organization_id],
        )
        response = await manager.order_types(request)

        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "order_types")

    async def test_get_payment_types_with_request(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение типов платежей через полный запрос."""
        from iikocloud_client import PaymentTypesPaymentTypesRequest

        request = PaymentTypesPaymentTypesRequest(
            organizationIds=[organization_id],
        )
        response = await manager.payment_types(request)

        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "payment_types")

    async def test_get_discounts_with_request(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение скидок через полный запрос."""
        from iikocloud_client import DiscountsDiscountsRequest

        request = DiscountsDiscountsRequest(
            organizationIds=[organization_id],
        )
        response = await manager.discounts(request)

        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "discounts")

    async def test_get_removal_types_with_request(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """Получение типов удаления через полный запрос."""
        from iikocloud_client import RemovalTypesRemovalTypesRequest

        request = RemovalTypesRemovalTypesRequest(
            organizationIds=[organization_id],
        )
        response = await manager.removal_types(request)

        assert response is not None
        assert hasattr(response, "correlation_id")
        assert hasattr(response, "removal_types")
