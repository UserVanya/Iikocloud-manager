"""Базовый класс и учётные данные для всех миксинов IikoCloudApiClientManager."""

import asyncio
import hashlib
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, fields
from enum import Enum
from typing import TypeVar, cast
from uuid import UUID

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


def as_uuid(value: str | UUID) -> UUID:
    """Привести идентификатор (organization_id, customer_id, ...) к UUID."""
    if isinstance(value, UUID):
        return value
    return UUID(value)


def _requests_per_second(config: RateLimitConfig) -> float:
    """Скорость лимита в запросах в секунду."""
    return config.max_requests / config.time_window_seconds


def _is_unauthorized(error: BaseException) -> bool:
    """401 ли это (типизированное исключение SDK или любое со ``status == 401``)."""
    return isinstance(error, UnauthorizedException) or (
        getattr(error, "status", None) == 401
    )


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
        """Создать из Pydantic settings (имена полей совпадают 1:1)."""
        return cls(
            **{
                field.name: RateLimitConfig(
                    max_requests=getattr(settings, field.name).max_requests,
                    time_window_seconds=getattr(
                        settings, field.name
                    ).time_window_seconds,
                )
                for field in fields(cls)
            }
        )

    def for_method(self, method: ApiMethod) -> RateLimitConfig:
        """Получить конфигурацию rate limit для метода.

        ``ApiMethod.<X>.value`` совпадает с именем поля (Locked Names),
        поэтому отдельная таблица соответствия не нужна.
        """
        return cast(RateLimitConfig, getattr(self, method.value))

    def compute_global_limit(self) -> RateLimitConfig:
        """Вычислить глобальный лимит как самый свободный (max RPS)."""
        limits = (
            cast(RateLimitConfig, getattr(self, field.name)) for field in fields(self)
        )
        return max(limits, key=_requests_per_second)


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

    async def _acquire_limits(self, method: ApiMethod) -> None:
        """Занять слот в глобальном и per-method rate limits."""
        await self._global_limiter.acquire()
        await self._get_method_limiter(method).acquire()

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
        2. acquire global + method limits
        3. capture token_version (именно здесь: ожидание лимитера может длиться
           минуты, и версия, снятая до ожидания, устареет — тогда refresh был бы
           ошибочно пропущен как «уже обновлён другой корутиной»)
        4. call
        5. on 401 → refresh_token_if_401(version_before); retry once if refreshed
        6. other errors re-raise
        """
        token_manager = await self._ensure_token_manager()
        logger.debug("Вызов API метода: %s", method.value)

        retried = False
        while True:
            await self._acquire_limits(method)
            version_before = token_manager.token_version
            try:
                result = await api_call()
            except Exception as exc:
                if not _is_unauthorized(exc):
                    logger.error(
                        "Ошибка API при вызове метода %s: %s",
                        method.value,
                        exc,
                    )
                    raise
                if retried:
                    # Один retry уже был — второй 401 отдаём наверх.
                    raise

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
                retried = True
            else:
                logger.debug("Метод %s выполнен успешно", method.value)
                return result
