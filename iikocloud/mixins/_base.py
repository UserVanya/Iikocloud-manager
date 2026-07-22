"""Базовый класс и учётные данные для всех миксинов IikoCloudApiClientManager."""

import asyncio
import hashlib
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from iikocloud_client import (
    ApiClient,
    AuthorizationApi,
    Configuration,
    CustomersApi,
    DictionariesApi,
    MenuApi,
    OrganizationsApi,
    TerminalGroupsApi,
)
from iikocloud_client.exceptions import UnauthorizedException

from iikocloud.config_reader import MethodRateLimitsSettings
from iikocloud.rate_limiter import (
    GlobalRateLimiter,
    RateLimitConfig,
    TokenBucketRateLimiter,
)
from iikocloud.token_manager import TokenManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ApiMethod(Enum):
    """Методы API для rate limiting (Locked Names)."""

    AUTH = "auth"

    # Organizations
    GET_ORGANIZATIONS = "get_organizations"
    GET_ORGANIZATION_SETTINGS = "get_organization_settings"

    # Customers
    CREATE_OR_UPDATE_CUSTOMER = "create_or_update_customer"
    GET_CUSTOMER_INFO = "get_customer_info"
    DELETE_CUSTOMERS = "delete_customers"
    RESTORE_CUSTOMERS = "restore_customers"

    # Terminal Groups
    GET_TERMINAL_GROUPS = "get_terminal_groups"
    CHECK_TERMINAL_GROUPS_AVAILABILITY = "check_terminal_groups_availability"

    # Menu
    GET_EXTERNAL_MENUS = "get_external_menus"
    GET_EXTERNAL_MENU_BY_ID = "get_external_menu_by_id"
    GET_STOP_LISTS = "get_stop_lists"

    # Dictionaries
    GET_CANCEL_CAUSES = "get_cancel_causes"
    GET_DELIVERY_ORDER_TYPES = "get_delivery_order_types"
    GET_PAYMENT_TYPES = "get_payment_types"
    GET_DISCOUNTS = "get_discounts"
    GET_REMOVAL_TYPES = "get_removal_types"
    GET_TIPS_TYPES = "get_tips_types"


@dataclass
class ApiCredentials:
    """Учётные данные для iikocloud (auth v2).

    Attributes:
        api_key: API-ключ
        app_id: Идентификатор приложения
        client_secret: Секрет клиента
    """

    api_key: str
    app_id: str
    client_secret: str

    @property
    def key_id(self) -> str:
        """Fingerprint api_key:app_id для Multitone (не manual field)."""
        return hashlib.sha1(
            f"{self.api_key}:{self.app_id}".encode()
        ).hexdigest()[:16]


@dataclass
class MethodRateLimits:
    """Конфигурация rate limits для каждого метода API."""

    auth: RateLimitConfig
    get_organizations: RateLimitConfig
    get_organization_settings: RateLimitConfig
    create_or_update_customer: RateLimitConfig
    get_customer_info: RateLimitConfig
    delete_customers: RateLimitConfig
    restore_customers: RateLimitConfig
    get_terminal_groups: RateLimitConfig
    check_terminal_groups_availability: RateLimitConfig
    get_external_menus: RateLimitConfig
    get_external_menu_by_id: RateLimitConfig
    get_stop_lists: RateLimitConfig
    get_cancel_causes: RateLimitConfig
    get_delivery_order_types: RateLimitConfig
    get_payment_types: RateLimitConfig
    get_discounts: RateLimitConfig
    get_removal_types: RateLimitConfig
    get_tips_types: RateLimitConfig

    @classmethod
    def from_settings(cls, settings: MethodRateLimitsSettings) -> "MethodRateLimits":
        """Создать из Pydantic settings."""

        def _cfg(field_name: str) -> RateLimitConfig:
            field = getattr(settings, field_name)
            return RateLimitConfig(
                max_requests=field.max_requests,
                time_window_seconds=field.time_window_seconds,
            )

        return cls(
            auth=_cfg("auth"),
            get_organizations=_cfg("get_organizations"),
            get_organization_settings=_cfg("get_organization_settings"),
            create_or_update_customer=_cfg("create_or_update_customer"),
            get_customer_info=_cfg("get_customer_info"),
            delete_customers=_cfg("delete_customers"),
            restore_customers=_cfg("restore_customers"),
            get_terminal_groups=_cfg("get_terminal_groups"),
            check_terminal_groups_availability=_cfg(
                "check_terminal_groups_availability"
            ),
            get_external_menus=_cfg("get_external_menus"),
            get_external_menu_by_id=_cfg("get_external_menu_by_id"),
            get_stop_lists=_cfg("get_stop_lists"),
            get_cancel_causes=_cfg("get_cancel_causes"),
            get_delivery_order_types=_cfg("get_delivery_order_types"),
            get_payment_types=_cfg("get_payment_types"),
            get_discounts=_cfg("get_discounts"),
            get_removal_types=_cfg("get_removal_types"),
            get_tips_types=_cfg("get_tips_types"),
        )

    def for_method(self, method: ApiMethod) -> RateLimitConfig:
        """Получить конфигурацию rate limit для метода."""
        mapping = {
            ApiMethod.AUTH: self.auth,
            ApiMethod.GET_ORGANIZATIONS: self.get_organizations,
            ApiMethod.GET_ORGANIZATION_SETTINGS: self.get_organization_settings,
            ApiMethod.CREATE_OR_UPDATE_CUSTOMER: self.create_or_update_customer,
            ApiMethod.GET_CUSTOMER_INFO: self.get_customer_info,
            ApiMethod.DELETE_CUSTOMERS: self.delete_customers,
            ApiMethod.RESTORE_CUSTOMERS: self.restore_customers,
            ApiMethod.GET_TERMINAL_GROUPS: self.get_terminal_groups,
            ApiMethod.CHECK_TERMINAL_GROUPS_AVAILABILITY: (
                self.check_terminal_groups_availability
            ),
            ApiMethod.GET_EXTERNAL_MENUS: self.get_external_menus,
            ApiMethod.GET_EXTERNAL_MENU_BY_ID: self.get_external_menu_by_id,
            ApiMethod.GET_STOP_LISTS: self.get_stop_lists,
            ApiMethod.GET_CANCEL_CAUSES: self.get_cancel_causes,
            ApiMethod.GET_DELIVERY_ORDER_TYPES: self.get_delivery_order_types,
            ApiMethod.GET_PAYMENT_TYPES: self.get_payment_types,
            ApiMethod.GET_DISCOUNTS: self.get_discounts,
            ApiMethod.GET_REMOVAL_TYPES: self.get_removal_types,
            ApiMethod.GET_TIPS_TYPES: self.get_tips_types,
        }
        return mapping[method]

    def compute_global_limit(self) -> RateLimitConfig:
        """Вычислить глобальный лимит как самый свободный (max RPS)."""
        all_limits = [
            self.auth,
            self.get_organizations,
            self.get_organization_settings,
            self.create_or_update_customer,
            self.get_customer_info,
            self.delete_customers,
            self.restore_customers,
            self.get_terminal_groups,
            self.check_terminal_groups_availability,
            self.get_external_menus,
            self.get_external_menu_by_id,
            self.get_stop_lists,
            self.get_cancel_causes,
            self.get_delivery_order_types,
            self.get_payment_types,
            self.get_discounts,
            self.get_removal_types,
            self.get_tips_types,
        ]

        max_rate = 0.0
        best_limit = all_limits[0]
        for limit in all_limits:
            rate = limit.max_requests / limit.time_window_seconds
            if rate > max_rate:
                max_rate = rate
                best_limit = limit
        return best_limit


def default_method_limits() -> MethodRateLimits:
    """Дефолтные лимиты из MethodRateLimitsSettings defaults."""
    return MethodRateLimits.from_settings(MethodRateLimitsSettings())


class _ManagerBase:
    """Базовый класс для миксинов IikoCloudApiClientManager.

    Объявляет разделяемое состояние и инфраструктуру:
    lazy API-клиенты, ensure_token_manager, execute_with_retry.
    Фактическая инициализация — в IikoCloudApiClientManager.__init__.
    """

    _credentials: ApiCredentials
    _config: Configuration
    _api_client: ApiClient
    _token_manager: TokenManager | None
    _init_lock: asyncio.Lock
    _global_limiter: GlobalRateLimiter
    _method_limits: MethodRateLimits
    _method_limiters: dict[ApiMethod, TokenBucketRateLimiter]

    _authorization_api: AuthorizationApi | None
    _organizations_api: OrganizationsApi | None
    _customers_api: CustomersApi | None
    _terminal_groups_api: TerminalGroupsApi | None
    _menu_api: MenuApi | None
    _dictionaries_api: DictionariesApi | None

    # ========== Lazy-геттеры API-клиентов ==========

    async def get_authorization_api(self) -> AuthorizationApi:
        """Получить клиент AuthorizationApi."""
        await self._ensure_token_manager()
        if self._authorization_api is None:
            self._authorization_api = AuthorizationApi(api_client=self._api_client)
        return self._authorization_api

    async def get_organizations_api(self) -> OrganizationsApi:
        """Получить клиент OrganizationsApi."""
        await self._ensure_token_manager()
        if self._organizations_api is None:
            self._organizations_api = OrganizationsApi(api_client=self._api_client)
        return self._organizations_api

    async def get_customers_api(self) -> CustomersApi:
        """Получить клиент CustomersApi."""
        await self._ensure_token_manager()
        if self._customers_api is None:
            self._customers_api = CustomersApi(api_client=self._api_client)
        return self._customers_api

    async def get_terminal_groups_api(self) -> TerminalGroupsApi:
        """Получить клиент TerminalGroupsApi."""
        await self._ensure_token_manager()
        if self._terminal_groups_api is None:
            self._terminal_groups_api = TerminalGroupsApi(api_client=self._api_client)
        return self._terminal_groups_api

    async def get_menu_api(self) -> MenuApi:
        """Получить клиент MenuApi."""
        await self._ensure_token_manager()
        if self._menu_api is None:
            self._menu_api = MenuApi(api_client=self._api_client)
        return self._menu_api

    async def get_dictionaries_api(self) -> DictionariesApi:
        """Получить клиент DictionariesApi."""
        await self._ensure_token_manager()
        if self._dictionaries_api is None:
            self._dictionaries_api = DictionariesApi(api_client=self._api_client)
        return self._dictionaries_api

    # ========== Инфраструктура ==========

    def _get_method_limiter(self, method: ApiMethod) -> TokenBucketRateLimiter:
        """Получить лимитер для метода API."""
        return self._method_limiters[method]

    async def _with_limits(
        self, method: ApiMethod, func: Callable[[], Awaitable[T]]
    ) -> T:
        """Выполнить функцию с глобальным и per-method rate limits."""
        await self._global_limiter.acquire()
        await self._get_method_limiter(method).acquire()
        return await func()

    async def _ensure_token_manager(self) -> TokenManager:
        """Обеспечить TokenManager с валидным токеном (double-check lock)."""
        if self._token_manager is not None:
            return self._token_manager

        async with self._init_lock:
            if self._token_manager is not None:
                return self._token_manager

            tm = await TokenManager.get_instance(
                api_client=self._api_client,
                api_key=self._credentials.api_key,
                app_id=self._credentials.app_id,
                client_secret=self._credentials.client_secret,
                key_id=self._credentials.key_id,
            )
            await tm.ensure_token_with_limits(
                acquire_global=self._global_limiter.acquire,
                acquire_auth=self._method_limiters[ApiMethod.AUTH].acquire,
            )
            self._token_manager = tm

        return self._token_manager

    async def execute_with_retry(
        self, method: ApiMethod, api_call: Callable[[], Awaitable[T]]
    ) -> T:
        """Выполнить API-вызов с rate limits и одним retry при 401.

        1. ensure token
        2. capture token_version
        3. acquire global + method limits
        4. call
        5. on 401 → refresh_token_if_401(version_before); retry once if refreshed
        6. other errors re-raise
        """
        token_manager = await self._ensure_token_manager()
        version_before = token_manager.token_version
        logger.debug("Вызов API метода: %s", method.value)

        try:
            result = await self._with_limits(method, api_call)
            logger.debug("Метод %s выполнен успешно", method.value)
            return result
        except UnauthorizedException as exc:
            refreshed = await token_manager.refresh_token_if_401(
                exc,
                acquire_global=self._global_limiter.acquire,
                acquire_auth=self._method_limiters[ApiMethod.AUTH].acquire,
                version_before=version_before,
            )
            if not refreshed:
                raise
            logger.debug(
                "Токен обновлён для метода %s, повторяем запрос",
                method.value,
            )
            return await self._with_limits(method, api_call)
        except Exception as exc:
            if getattr(exc, "status", None) == 401:
                refreshed = await token_manager.refresh_token_if_401(
                    exc,
                    acquire_global=self._global_limiter.acquire,
                    acquire_auth=self._method_limiters[ApiMethod.AUTH].acquire,
                    version_before=version_before,
                )
                if not refreshed:
                    raise
                logger.debug(
                    "Токен обновлён для метода %s, повторяем запрос",
                    method.value,
                )
                return await self._with_limits(method, api_call)

            logger.error(
                "Ошибка API при вызове метода %s: %s",
                method.value,
                exc,
            )
            raise
