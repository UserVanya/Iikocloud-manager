"""Фасад iikocloud API: Multitone + rate-limited execute_with_retry."""

import asyncio
import logging

from iikocloud_client import (
    ApiClient,
    AuthorizationApi,
    Configuration,
    CustomersApi,
    DeliveriesCreateAndUpdateApi,
    DictionariesApi,
    MenuApi,
    OrganizationsApi,
    TerminalGroupsApi,
)

from iikocloud.config_reader import IikoCloudConfig
from iikocloud.mixins._base import (
    ApiCredentials,
    ApiMethod,
    MethodRateLimits,
    _ManagerBase,
    default_method_limits,
)
from iikocloud.mixins.customers.helpers import CustomersHelpersMixin
from iikocloud.mixins.deliveries.helpers import DeliveriesHelpersMixin
from iikocloud.mixins.dictionaries.helpers import DictionariesHelpersMixin
from iikocloud.mixins.menu.helpers import MenuHelpersMixin
from iikocloud.mixins.organizations.helpers import OrganizationsHelpersMixin
from iikocloud.mixins.terminal_groups.helpers import TerminalGroupsHelpersMixin
from iikocloud.rate_limiter import GlobalRateLimiter, TokenBucketRateLimiter
from iikocloud.token_manager import TokenManager

logger = logging.getLogger(__name__)

# Re-export for callers that import credentials / enums from this module.
__all__ = [
    "ApiCredentials",
    "ApiMethod",
    "IikoCloudApiClientManager",
    "MethodRateLimits",
]


class IikoCloudApiClientManager(
    DeliveriesHelpersMixin,
    CustomersHelpersMixin,
    DictionariesHelpersMixin,
    MenuHelpersMixin,
    OrganizationsHelpersMixin,
    TerminalGroupsHelpersMixin,
    _ManagerBase,
):
    """Multitone-фасад для работы с iikocloud API.

    Содержит: ApiClient, TokenManager, глобальный лимитер, лимитеры по методам.
    Domain-методы — через mixins: organizations, customers, terminal_groups,
    menu, dictionaries, deliveries.

    Конкурентность:
        Экземпляр безопасен для параллельных вызовов из нескольких задач
        ОДНОГО event loop. Между разными asyncio.run / новым loop —
        обязательно close_all().
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

        Используйте get_instance() / from_config() для получения экземпляра.
        """
        self._credentials = credentials
        self._global_limiter = global_limiter
        self._method_limits = method_limits

        # Per-method token buckets
        self._method_limiters: dict[ApiMethod, TokenBucketRateLimiter] = {
            method: TokenBucketRateLimiter(method_limits.for_method(method))
            for method in ApiMethod
        }

        # SDK default host (https://api-ru.iiko.services) — no host override
        self._config = Configuration()
        self._api_client = ApiClient(configuration=self._config)

        self._token_manager: TokenManager | None = None
        self._init_lock = asyncio.Lock()

        # Lazy API client caches
        self._authorization_api: AuthorizationApi | None = None
        self._organizations_api: OrganizationsApi | None = None
        self._customers_api: CustomersApi | None = None
        self._terminal_groups_api: TerminalGroupsApi | None = None
        self._menu_api: MenuApi | None = None
        self._dictionaries_api: DictionariesApi | None = None
        self._deliveries_create_and_update_api: DeliveriesCreateAndUpdateApi | None = (
            None
        )

        logger.debug(
            "Создан экземпляр IikoCloudApiClientManager для key_id=%s",
            credentials.key_id,
        )

    @classmethod
    async def get_instance(
        cls,
        credentials: ApiCredentials,
        method_limits: MethodRateLimits | None = None,
    ) -> "IikoCloudApiClientManager":
        """Получить или создать экземпляр менеджера для credentials.key_id."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            key = credentials.key_id
            if key not in cls._instances:
                if method_limits is None:
                    method_limits = default_method_limits()

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
        """Создать экземпляр из IikoCloudConfig (auth v2 + rate limits)."""
        creds = ApiCredentials(
            api_key=config.api_key.get_secret_value(),
            app_id=config.app_id,
            client_secret=config.client_secret.get_secret_value(),
        )
        limits = MethodRateLimits.from_settings(config.rate_limits)
        return await cls.get_instance(creds, limits)

    @classmethod
    async def close_all(cls) -> None:
        """Закрыть все соединения и сбросить Multitone / limiters / tokens.

        Также сбрасывает классовый lock (привязан к event loop).
        """
        instance_count = len(cls._instances)

        # Сбрасываем токены до закрытия сессий, пока они ещё живы
        await TokenManager.close_all()

        try:
            for manager in cls._instances.values():
                try:
                    await manager._api_client.close()  # type: ignore[no-untyped-call]
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Не удалось закрыть ApiClient: %s", exc)
        finally:
            # Реестр сбрасывается всегда: иначе get_instance() вернёт менеджер
            # с уже закрытым HTTP-клиентом.
            cls._instances.clear()
            cls._lock = None
            GlobalRateLimiter.reset_instance()

        logger.debug("Закрыты все соединения (%d экземпляров)", instance_count)
