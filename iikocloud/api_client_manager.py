"""Фасад iikocloud API: per-method rate limiting, retry при 401.

Реализует Multitone паттерн — один экземпляр на key_id.
Глобальный rate limit автоматически вычисляется как самый свободный
из всех методов.
"""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar
from uuid import UUID

from iikocloud_client import (
    ApiClient,
    Configuration,
    CustomerCreateOrUpdateCustomerRequest,
    CustomerCreateOrUpdateCustomerResponse,
    CustomerDeleteCustomersRequest,
    CustomerDeleteCustomersResponse,
    CustomerGetCustomerInfoByPhoneRequest,
    CustomerGetCustomerInfoRequest,
    CustomerGetCustomerInfoResponse,
    CustomerRestoreCustomersRequest,
    CustomerRestoreCustomersResponse,
    CustomersApi,
    ExternalMenuV2,
    ExternalMenuV3,
    ExternalMenuV4,
    MenuApi,
    MenuByIdPost200Response,
    NomenclatureMenuRequest,
    NomenclatureMenusDataResponse,
    OrdersApi,
    OrganizationsApi,
    OrganizationsGetOrganizationsRequest,
    OrganizationsGetOrganizationsResponse,
    StopListsStopListsRequest,
    StopListsStopListsResponse,
    TerminalGroupsApi,
    TerminalsTerminalGroupsIsAliveRequest,
    TerminalsTerminalGroupsIsAliveResponse,
    TerminalsTerminalGroupsRequest,
    TerminalsTerminalGroupsResponse,
)
from iikocloud_client.exceptions import UnauthorizedException

from iikocloud.config_reader import IikoCloudConfig, MethodRateLimitsSettings
from iikocloud.rate_limiter import (
    GlobalRateLimiter,
    RateLimitConfig,
    TokenBucketRateLimiter,
)
from iikocloud.token_manager import TokenManager

T = TypeVar("T")


class ApiMethod(Enum):
    """Методы API для rate limiting."""

    # Авторизация
    AUTH = "auth"

    # Organizations
    GET_ORGANIZATIONS = "get_organizations"

    # Customers
    CREATE_OR_UPDATE_CUSTOMER = "create_or_update_customer"
    GET_CUSTOMER_INFO = "get_customer_info"
    DELETE_CUSTOMERS = "delete_customers"
    RESTORE_CUSTOMERS = "restore_customers"

    # Terminal Groups
    GET_TERMINAL_GROUPS = "get_terminal_groups"
    CHECK_TERMINAL_GROUPS_ALIVE = "check_terminal_groups_alive"

    # Menu
    GET_EXTERNAL_MENUS = "get_external_menus"
    GET_MENU_BY_ID = "get_menu_by_id"
    GET_STOP_LISTS = "get_stop_lists"


@dataclass
class ApiCredentials:
    """Учетные данные для iikocloud.

    Attributes:
        api_login: Логин для получения токена
        key_id: Уникальный идентификатор ключа (для multitone)
    """

    api_login: str
    key_id: str


@dataclass
class MethodRateLimits:
    """Конфигурация rate limits для каждого метода API.

    Attributes:
        auth: Лимит для авторизации
        get_organizations: Лимит для получения организаций
        create_or_update_customer: Лимит для создания/обновления клиента
        get_customer_info: Лимит для получения информации о клиенте
        delete_customers: Лимит для удаления клиентов
        restore_customers: Лимит для восстановления клиентов
        get_terminal_groups: Лимит для получения терминальных групп
        check_terminal_groups_alive: Лимит для проверки доступности групп
        get_external_menus: Лимит для получения внешних меню
        get_menu_by_id: Лимит для получения меню по ID
        get_stop_lists: Лимит для получения стоп-листов
    """

    auth: RateLimitConfig
    get_organizations: RateLimitConfig
    create_or_update_customer: RateLimitConfig
    get_customer_info: RateLimitConfig
    delete_customers: RateLimitConfig
    restore_customers: RateLimitConfig
    get_terminal_groups: RateLimitConfig
    check_terminal_groups_alive: RateLimitConfig
    get_external_menus: RateLimitConfig
    get_menu_by_id: RateLimitConfig
    get_stop_lists: RateLimitConfig

    @classmethod
    def from_settings(cls, settings: MethodRateLimitsSettings) -> "MethodRateLimits":
        """Создать из Pydantic settings."""
        return cls(
            auth=RateLimitConfig(
                max_requests=settings.auth.max_requests,
                time_window_seconds=settings.auth.time_window_seconds,
            ),
            get_organizations=RateLimitConfig(
                max_requests=settings.get_organizations.max_requests,
                time_window_seconds=settings.get_organizations.time_window_seconds,
            ),
            create_or_update_customer=RateLimitConfig(
                max_requests=settings.create_or_update_customer.max_requests,
                time_window_seconds=settings.create_or_update_customer.time_window_seconds,
            ),
            get_customer_info=RateLimitConfig(
                max_requests=settings.get_customer_info.max_requests,
                time_window_seconds=settings.get_customer_info.time_window_seconds,
            ),
            delete_customers=RateLimitConfig(
                max_requests=settings.delete_customers.max_requests,
                time_window_seconds=settings.delete_customers.time_window_seconds,
            ),
            restore_customers=RateLimitConfig(
                max_requests=settings.restore_customers.max_requests,
                time_window_seconds=settings.restore_customers.time_window_seconds,
            ),
            get_terminal_groups=RateLimitConfig(
                max_requests=settings.get_terminal_groups.max_requests,
                time_window_seconds=settings.get_terminal_groups.time_window_seconds,
            ),
            check_terminal_groups_alive=RateLimitConfig(
                max_requests=settings.check_terminal_groups_alive.max_requests,
                time_window_seconds=settings.check_terminal_groups_alive.time_window_seconds,
            ),
            get_external_menus=RateLimitConfig(
                max_requests=settings.get_external_menus.max_requests,
                time_window_seconds=settings.get_external_menus.time_window_seconds,
            ),
            get_menu_by_id=RateLimitConfig(
                max_requests=settings.get_menu_by_id.max_requests,
                time_window_seconds=settings.get_menu_by_id.time_window_seconds,
            ),
            get_stop_lists=RateLimitConfig(
                max_requests=settings.get_stop_lists.max_requests,
                time_window_seconds=settings.get_stop_lists.time_window_seconds,
            ),
        )

    def get_by_method(self, method: ApiMethod) -> RateLimitConfig:
        """Получить конфигурацию по методу."""
        mapping = {
            ApiMethod.AUTH: self.auth,
            ApiMethod.GET_ORGANIZATIONS: self.get_organizations,
            ApiMethod.CREATE_OR_UPDATE_CUSTOMER: self.create_or_update_customer,
            ApiMethod.GET_CUSTOMER_INFO: self.get_customer_info,
            ApiMethod.DELETE_CUSTOMERS: self.delete_customers,
            ApiMethod.RESTORE_CUSTOMERS: self.restore_customers,
            ApiMethod.GET_TERMINAL_GROUPS: self.get_terminal_groups,
            ApiMethod.CHECK_TERMINAL_GROUPS_ALIVE: self.check_terminal_groups_alive,
            ApiMethod.GET_EXTERNAL_MENUS: self.get_external_menus,
            ApiMethod.GET_MENU_BY_ID: self.get_menu_by_id,
            ApiMethod.GET_STOP_LISTS: self.get_stop_lists,
        }
        return mapping[method]

    def compute_global_limit(self) -> RateLimitConfig:
        """Вычислить глобальный лимит как самый свободный."""
        all_limits = [
            self.auth,
            self.get_organizations,
            self.create_or_update_customer,
            self.get_customer_info,
            self.delete_customers,
            self.restore_customers,
            self.get_terminal_groups,
            self.check_terminal_groups_alive,
            self.get_external_menus,
            self.get_menu_by_id,
            self.get_stop_lists,
        ]

        max_rate = 0.0
        best_limit = all_limits[0]

        for limit in all_limits:
            rate = limit.max_requests / limit.time_window_seconds
            if rate > max_rate:
                max_rate = rate
                best_limit = limit

        return best_limit


def _default_method_limits() -> MethodRateLimits:
    """Создать дефолтные лимиты для методов."""
    return MethodRateLimits(
        auth=RateLimitConfig(max_requests=1, time_window_seconds=5.0),
        get_organizations=RateLimitConfig(max_requests=1, time_window_seconds=10.0),
        create_or_update_customer=RateLimitConfig(
            max_requests=100, time_window_seconds=60.0
        ),
        get_customer_info=RateLimitConfig(max_requests=100, time_window_seconds=60.0),
        delete_customers=RateLimitConfig(max_requests=100, time_window_seconds=60.0),
        restore_customers=RateLimitConfig(max_requests=100, time_window_seconds=60.0),
        get_terminal_groups=RateLimitConfig(max_requests=10, time_window_seconds=60.0),
        check_terminal_groups_alive=RateLimitConfig(
            max_requests=10, time_window_seconds=60.0
        ),
        get_external_menus=RateLimitConfig(max_requests=1, time_window_seconds=1800.0),
        get_menu_by_id=RateLimitConfig(max_requests=5, time_window_seconds=60.0),
        get_stop_lists=RateLimitConfig(max_requests=10, time_window_seconds=60.0),
    )


class IikoCloudApiClientManager:
    """Multitone-фасад для работы с iikocloud API.

    Содержит: ApiClient, TokenManager, глобальный лимитер, лимитеры по методам.
    Предоставляет типизированные методы для работы с API.

    Использование:
        manager = await IikoCloudApiClientManager.get_instance(credentials, limits)
        orgs = await manager.get_organizations(request)
    """

    _instances: dict[str, "IikoCloudApiClientManager"] = {}
    _lock: asyncio.Lock | None = None

    def __init__(
        self,
        credentials: ApiCredentials,
        global_limiter: GlobalRateLimiter,
        method_limits: MethodRateLimits,
    ) -> None:
        """Инициализация менеджера (внутренний метод).

        Используйте get_instance() для получения экземпляра.
        """
        self._credentials = credentials
        self._global_limiter = global_limiter
        self._method_limits = method_limits

        # Создаём лимитеры для каждого метода API
        self._method_limiters: dict[ApiMethod, TokenBucketRateLimiter] = {
            method: TokenBucketRateLimiter(method_limits.get_by_method(method))
            for method in ApiMethod
        }

        self._config = Configuration()
        self._api_client = ApiClient(configuration=self._config)

        self._token_manager: TokenManager | None = None
        self._customers_api: CustomersApi | None = None
        self._organizations_api: OrganizationsApi | None = None
        self._terminal_groups_api: TerminalGroupsApi | None = None
        self._menu_api: MenuApi | None = None
        self._orders_api: OrdersApi | None = None

    @classmethod
    async def get_instance(
        cls,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits | None = None,
    ) -> "IikoCloudApiClientManager":
        """Получить или создать экземпляр менеджера для key_id.

        Args:
            credentials: Учетные данные API
            method_limits: Конфигурация rate limits для методов (опционально)

        Returns:
            Экземпляр IikoCloudApiClientManager
        """
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            key = credentials.key_id
            if key not in cls._instances:
                if method_limits is None:
                    method_limits = _default_method_limits()

                # Глобальный лимит = самый свободный из всех методов
                global_config = method_limits.compute_global_limit()
                global_rl = await GlobalRateLimiter.get_instance(global_config)

                cls._instances[key] = cls(
                    credentials=credentials,
                    global_limiter=global_rl,
                    method_limits=method_limits,
                )
            return cls._instances[key]

    @classmethod
    async def from_config(cls, config: IikoCloudConfig) -> "IikoCloudApiClientManager":
        """Создать экземпляр из конфигурации.

        Args:
            config: Конфигурация iikocloud из YAML-файла

        Returns:
            Экземпляр IikoCloudApiClientManager
        """
        credentials = ApiCredentials(
            api_login=config.api_login.get_secret_value(),
            key_id=config.key_id,
        )
        print(config.api_login.get_secret_value())
        method_limits = MethodRateLimits.from_settings(config.rate_limits)

        return await cls.get_instance(
            credentials=credentials,
            method_limits=method_limits,
        )

    @classmethod
    async def close_all(cls) -> None:
        """Закрыть все соединения и сбросить экземпляры."""
        for manager in cls._instances.values():
            await manager._api_client.close()  # type: ignore[no-untyped-call]
        cls._instances.clear()
        cls._lock = None
        GlobalRateLimiter.reset_instance()
        await TokenManager.close_all()

    async def _ensure_token_manager(self) -> TokenManager:
        """Обеспечить наличие token manager с токеном."""
        if self._token_manager is None:
            self._token_manager = await TokenManager.get_instance(
                api_client=self._api_client,
                api_login=self._credentials.api_login,
                key_id=self._credentials.key_id,
            )
            await self._token_manager.ensure_token_with_limits(
                acquire_global=self._global_limiter.acquire,
                acquire_auth=self._method_limiters[ApiMethod.AUTH].acquire,
            )
        return self._token_manager

    def _get_method_limiter(self, method: ApiMethod) -> TokenBucketRateLimiter:
        """Получить лимитер для метода API."""
        return self._method_limiters[method]

    async def _with_limits(
        self, method: ApiMethod, func: Callable[[], Awaitable[T]]
    ) -> T:
        """Выполнить функцию с применением rate limits."""
        await self._global_limiter.acquire()
        await self._get_method_limiter(method).acquire()
        return await func()

    async def execute_with_retry(
        self, method: ApiMethod, api_call: Callable[[], Awaitable[T]]
    ) -> T:
        """Выполнить API-вызов с rate limits и retry при 401.

        Args:
            method: Метод API для rate limiting
            api_call: Асинхронная функция вызова API

        Returns:
            Результат вызова

        Raises:
            Exception: Любые ошибки кроме 401 (они обрабатываются retry)
        """
        token_manager = await self._ensure_token_manager()

        try:
            return await self._with_limits(method, api_call)
        except UnauthorizedException as exc:
            await token_manager.refresh_token_if_401_with_limits(
                exc,
                acquire_global=self._global_limiter.acquire,
                acquire_auth=self._method_limiters[ApiMethod.AUTH].acquire,
            )
            return await self._with_limits(method, api_call)
        except Exception as exc:
            # Проверяем на 401 в других типах исключений
            if getattr(exc, "status", None) == 401:
                await token_manager.refresh_token_if_401_with_limits(
                    exc,
                    acquire_global=self._global_limiter.acquire,
                    acquire_auth=self._method_limiters[ApiMethod.AUTH].acquire,
                )
                return await self._with_limits(method, api_call)
            raise

    # ========== API Клиенты ==========

    async def get_customers_api(self) -> CustomersApi:
        """Получить клиент CustomersApi."""
        await self._ensure_token_manager()
        if self._customers_api is None:
            self._customers_api = CustomersApi(api_client=self._api_client)
        return self._customers_api

    async def get_organizations_api(self) -> OrganizationsApi:
        """Получить клиент OrganizationsApi."""
        await self._ensure_token_manager()
        if self._organizations_api is None:
            self._organizations_api = OrganizationsApi(api_client=self._api_client)
        return self._organizations_api

    async def get_menu_api(self) -> MenuApi:
        """Получить клиент MenuApi."""
        await self._ensure_token_manager()
        if self._menu_api is None:
            self._menu_api = MenuApi(api_client=self._api_client)
        return self._menu_api

    async def get_orders_api(self) -> OrdersApi:
        """Получить клиент OrdersApi."""
        await self._ensure_token_manager()
        if self._orders_api is None:
            self._orders_api = OrdersApi(api_client=self._api_client)
        return self._orders_api

    async def get_terminal_groups_api(self) -> TerminalGroupsApi:
        """Получить клиент TerminalGroupsApi."""
        await self._ensure_token_manager()
        if self._terminal_groups_api is None:
            self._terminal_groups_api = TerminalGroupsApi(api_client=self._api_client)
        return self._terminal_groups_api

    # ========== Основные методы: Customers ==========

    async def create_or_update_customer(
        self,
        request: CustomerCreateOrUpdateCustomerRequest,
    ) -> CustomerCreateOrUpdateCustomerResponse:
        """Создать или обновить клиента.

        Args:
            request: Запрос на создание/обновление клиента

        Returns:
            Ответ с информацией о клиенте
        """

        async def api_call() -> CustomerCreateOrUpdateCustomerResponse:
            api = await self.get_customers_api()
            return await api.loyalty_iiko_customer_create_or_update_post(
                customer_create_or_update_customer_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_OR_UPDATE_CUSTOMER, api_call
        )

    async def get_customer_info(
        self,
        request: CustomerGetCustomerInfoRequest,
    ) -> CustomerGetCustomerInfoResponse:
        """Получить информацию о клиенте.

        Args:
            request: Запрос с идентификатором клиента

        Returns:
            Информация о клиенте
        """

        async def api_call() -> CustomerGetCustomerInfoResponse:
            api = await self.get_customers_api()
            return await api.loyalty_iiko_customer_info_post(
                customer_get_customer_info_request=request
            )

        return await self.execute_with_retry(ApiMethod.GET_CUSTOMER_INFO, api_call)

    async def delete_customers(
        self,
        request: CustomerDeleteCustomersRequest,
    ) -> CustomerDeleteCustomersResponse:
        """Удалить клиентов.

        Args:
            request: Запрос на удаление клиентов

        Returns:
            Результат удаления
        """

        async def api_call() -> CustomerDeleteCustomersResponse:
            api = await self.get_customers_api()
            return await api.loyalty_iiko_delete_customers_post(
                customer_delete_customers_request=request
            )

        return await self.execute_with_retry(ApiMethod.DELETE_CUSTOMERS, api_call)

    async def restore_customers(
        self,
        request: CustomerRestoreCustomersRequest,
    ) -> CustomerRestoreCustomersResponse:
        """Восстановить клиентов.

        Args:
            request: Запрос на восстановление клиентов

        Returns:
            Результат восстановления
        """

        async def api_call() -> CustomerRestoreCustomersResponse:
            api = await self.get_customers_api()
            return await api.loyalty_iiko_restore_customers_post(
                customer_restore_customers_request=request
            )

        return await self.execute_with_retry(ApiMethod.RESTORE_CUSTOMERS, api_call)

    # ========== Основные методы: Organizations ==========

    async def organizations(
        self,
        request: OrganizationsGetOrganizationsRequest | None = None,
    ) -> OrganizationsGetOrganizationsResponse:
        """Получить список организаций.

        Args:
            request: Запрос на получение организаций

        Returns:
            Список организаций
        """
        if request is None:
            request = OrganizationsGetOrganizationsRequest()

        async def api_call() -> OrganizationsGetOrganizationsResponse:
            api = await self.get_organizations_api()
            return await api.organizations_post(
                organizations_get_organizations_request=request
            )

        return await self.execute_with_retry(ApiMethod.GET_ORGANIZATIONS, api_call)

    # ========== Основные методы: Terminal Groups ==========

    async def terminal_groups(
        self,
        request: TerminalsTerminalGroupsRequest,
    ) -> TerminalsTerminalGroupsResponse:
        """Получить список терминальных групп.

        Args:
            request: Запрос с ID организаций

        Returns:
            Список терминальных групп
        """

        async def api_call() -> TerminalsTerminalGroupsResponse:
            api = await self.get_terminal_groups_api()
            return await api.terminal_groups_post(
                terminals_terminal_groups_request=request
            )

        return await self.execute_with_retry(ApiMethod.GET_TERMINAL_GROUPS, api_call)

    async def terminal_groups_alive(
        self,
        request: TerminalsTerminalGroupsIsAliveRequest,
    ) -> TerminalsTerminalGroupsIsAliveResponse:
        """Проверить доступность терминальных групп.

        Args:
            request: Запрос с ID терминальных групп и организаций

        Returns:
            Информация о доступности терминальных групп
        """

        async def api_call() -> TerminalsTerminalGroupsIsAliveResponse:
            api = await self.get_terminal_groups_api()
            return await api.terminal_groups_is_alive_post(
                terminals_terminal_groups_is_alive_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHECK_TERMINAL_GROUPS_ALIVE, api_call
        )

    # ========== Основные методы: Menu ==========

    async def external_menus(self) -> NomenclatureMenusDataResponse:
        """Получить список внешних меню с ценовыми категориями.

        Returns:
            Список внешних меню
        """

        async def api_call() -> NomenclatureMenusDataResponse:
            api = await self.get_menu_api()
            return await api.menu_post()

        return await self.execute_with_retry(ApiMethod.GET_EXTERNAL_MENUS, api_call)

    async def menu_by_id(
        self,
        request: NomenclatureMenuRequest,
    ) -> MenuByIdPost200Response:
        """Получить внешнее меню по ID.

        Args:
            request: Запрос с ID организации и внешнего меню

        Returns:
            Данные внешнего меню
        """

        async def api_call() -> MenuByIdPost200Response:
            api = await self.get_menu_api()
            return await api.menu_by_id_post(nomenclature_menu_request=request)

        return await self.execute_with_retry(ApiMethod.GET_MENU_BY_ID, api_call)

    async def stop_lists(
        self,
        request: StopListsStopListsRequest,
    ) -> StopListsStopListsResponse:
        """Получить стоп-листы (товары, отсутствующие в наличии).

        Args:
            request: Запрос с ID организаций

        Returns:
            Стоп-листы организаций
        """

        async def api_call() -> StopListsStopListsResponse:
            api = await self.get_menu_api()
            return await api.stop_lists_post(stop_lists_stop_lists_request=request)

        return await self.execute_with_retry(ApiMethod.GET_STOP_LISTS, api_call)

    # ========== Вспомогательные методы: Customers ==========

    async def get_customer_by_phone(
        self,
        phone: str,
        organization_id: str,
    ) -> CustomerGetCustomerInfoResponse:
        """Получить информацию о клиенте по номеру телефона.

        Args:
            phone: Номер телефона клиента
            organization_id: ID организации

        Returns:
            Информация о клиенте
        """
        request = CustomerGetCustomerInfoByPhoneRequest(
            type="phone",
            organizationId=UUID(organization_id),
            phone=phone,
        )
        # Вызываем основной метод (без дублирования execute_with_retry)
        return await self.get_customer_info(request)

    async def logical_delete_customer(
        self,
        customer_id: str,
        organization_id: str,
    ) -> CustomerDeleteCustomersResponse:
        """Логически удалить клиента.

        Args:
            customer_id: ID клиента
            organization_id: ID организации

        Returns:
            Результат удаления
        """
        request = CustomerDeleteCustomersRequest(
            customerIds=[UUID(customer_id)],
            organizationId=UUID(organization_id),
        )
        return await self.delete_customers(request)

    async def logical_restore_customer(
        self,
        customer_id: str,
        organization_id: str,
    ) -> CustomerRestoreCustomersResponse:
        """Восстановить логически удаленного клиента.

        Args:
            customer_id: ID клиента
            organization_id: ID организации

        Returns:
            Результат восстановления
        """
        request = CustomerRestoreCustomersRequest(
            customerIds=[UUID(customer_id)],
            organizationId=UUID(organization_id),
        )
        return await self.restore_customers(request)

    # ========== Вспомогательные методы: Terminal Groups ==========

    async def get_terminal_groups_by_organization(
        self,
        organization_id: str,
        include_disabled: bool = False,
    ) -> TerminalsTerminalGroupsResponse:
        """Получить терминальные группы для конкретной организации.

        Args:
            organization_id: ID организации
            include_disabled: Включать отключённые группы

        Returns:
            Терминальные группы организации
        """
        request = TerminalsTerminalGroupsRequest(
            organizationIds=[UUID(organization_id)],
            includeDisabled=include_disabled,
        )
        return await self.terminal_groups(request)

    async def check_terminal_group_alive(
        self,
        terminal_group_id: str,
        organization_id: str,
    ) -> TerminalsTerminalGroupsIsAliveResponse:
        """Проверить доступность конкретной терминальной группы.

        Args:
            terminal_group_id: ID терминальной группы
            organization_id: ID организации

        Returns:
            Информация о доступности терминальной группы
        """
        request = TerminalsTerminalGroupsIsAliveRequest(
            organizationIds=[UUID(organization_id)],
            terminalGroupIds=[UUID(terminal_group_id)],
        )
        return await self.terminal_groups_alive(request)

    # ========== Вспомогательные методы: Menu ==========

    async def get_menu_by_id_and_organization_v2(
        self,
        organization_id: str,
        external_menu_id: str,
    ) -> ExternalMenuV2:
        """Получить внешнее меню для организации.

        Args:
            organization_id: ID организации
            external_menu_id: ID внешнего меню

        Returns:
            Данные внешнего меню
        """
        request = NomenclatureMenuRequest(
            organizationIds=[UUID(organization_id)],
            externalMenuId=external_menu_id,
            version=2,
        )
        return await self.menu_by_id(request) # type: ignore
    async def get_menu_by_id_and_organization_v3(
        self,
        organization_id: str,
        external_menu_id: str,
    ) -> ExternalMenuV3:
        """Получить внешнее меню для организации.

        Args:
            organization_id: ID организации
            external_menu_id: ID внешнего меню

        Returns:
            Данные внешнего меню
        """
        request = NomenclatureMenuRequest(
            organizationIds=[UUID(organization_id)],
            externalMenuId=external_menu_id,
            version=3,
        )
        return await self.menu_by_id(request) # type: ignore

    async def get_menu_by_id_and_organization_v4(
        self,
        organization_id: str,
        external_menu_id: str,
    ) -> ExternalMenuV4:
        """Получить внешнее меню для организации.

        Args:
            organization_id: ID организации
            external_menu_id: ID внешнего меню

        Returns:
            Данные внешнего меню
        """
        request = NomenclatureMenuRequest(
            organizationIds=[UUID(organization_id)],
            externalMenuId=external_menu_id,
            version=4,
        )
        return await self.menu_by_id(request) # type: ignore

    async def get_stop_lists_by_organization(
        self,
        organization_ids: list[str],
    ) -> StopListsStopListsResponse:
        """Получить стоп-листы для организаций.

        Args:
            organization_ids: Список ID организаций

        Returns:
            Стоп-листы организаций
        """
        request = StopListsStopListsRequest(
            organizationIds=[UUID(org_id) for org_id in organization_ids],
        )
        return await self.stop_lists(request)
