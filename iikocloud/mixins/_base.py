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
    AddressesApi,
    ApiClient,
    AuthorizationApi,
    Configuration,
    CustomerCategoriesApi,
    CustomersApi,
    DeliveriesCreateAndUpdateApi,
    DeliveriesRetrieveApi,
    DeliveryRestrictionsApi,
    DictionariesApi,
    DiscountsAndPromotionsApi,
    DraftsApi,
    EmployeesApi,
    MarketingSourcesApi,
    MenuApi,
    MessagesApi,
    NotificationsApi,
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

    # Customers — cards / programs / wallets
    ADD_CUSTOMER_MAGNET_CARD = "add_customer_magnet_card"
    REMOVE_CUSTOMER_MAGNET_CARD = "remove_customer_magnet_card"
    ADD_CUSTOMER_TO_PROGRAM = "add_customer_to_program"
    HOLD_CUSTOMER_BALANCE = "hold_customer_balance"
    CANCEL_CUSTOMER_BALANCE_HOLD = "cancel_customer_balance_hold"
    TOP_UP_CUSTOMER_BALANCE = "top_up_customer_balance"
    WITHDRAW_CUSTOMER_BALANCE = "withdraw_customer_balance"
    GET_LOYALTY_COUNTERS = "get_loyalty_counters"

    # Customer Categories
    GET_CUSTOMER_CATEGORIES = "get_customer_categories"
    ADD_CUSTOMER_CATEGORY = "add_customer_category"
    REMOVE_CUSTOMER_CATEGORY = "remove_customer_category"

    # Terminal Groups
    GET_TERMINAL_GROUPS = "get_terminal_groups"
    CHECK_TERMINAL_GROUPS_AVAILABILITY = "check_terminal_groups_availability"

    # Menu
    GET_EXTERNAL_MENUS = "get_external_menus"
    GET_EXTERNAL_MENU_BY_ID = "get_external_menu_by_id"
    GET_STOP_LISTS = "get_stop_lists"

    # Menu — stop lists / nomenclature / combos
    ADD_PRODUCTS_TO_STOP_LIST = "add_products_to_stop_list"
    REMOVE_PRODUCTS_FROM_STOP_LIST = "remove_products_from_stop_list"
    CLEAR_STOP_LIST = "clear_stop_list"
    CHECK_PRODUCTS_IN_STOP_LIST = "check_products_in_stop_list"
    GET_NOMENCLATURE = "get_nomenclature"
    GET_COMBOS_INFO = "get_combos_info"
    CALCULATE_COMBO_PRICE = "calculate_combo_price"

    # Dictionaries
    GET_CANCEL_CAUSES = "get_cancel_causes"
    GET_DELIVERY_ORDER_TYPES = "get_delivery_order_types"
    GET_PAYMENT_TYPES = "get_payment_types"
    GET_DISCOUNTS = "get_discounts"
    GET_REMOVAL_TYPES = "get_removal_types"
    GET_TIPS_TYPES = "get_tips_types"

    # Deliveries (create & update)
    CREATE_DELIVERY_ORDER = "create_delivery_order"
    ADD_DELIVERY_ORDER_ITEMS = "add_delivery_order_items"
    ADD_DELIVERY_ORDER_PAYMENTS = "add_delivery_order_payments"
    CANCEL_DELIVERY_ORDER = "cancel_delivery_order"
    CANCEL_DELIVERY_CONFIRMATION = "cancel_delivery_confirmation"
    CONFIRM_DELIVERY = "confirm_delivery"
    CHANGE_DELIVERY_COMMENT = "change_delivery_comment"
    CHANGE_DELIVERY_COMPLETE_BEFORE = "change_delivery_complete_before"
    CHANGE_DELIVERY_DRIVER_INFO = "change_delivery_driver_info"
    CHANGE_DELIVERY_EXTERNAL_DATA = "change_delivery_external_data"
    CHANGE_DELIVERY_OPERATOR = "change_delivery_operator"
    CHANGE_DELIVERY_PAYMENTS = "change_delivery_payments"
    CHANGE_DELIVERY_POINT = "change_delivery_point"
    CHANGE_DELIVERY_SERVICE_TYPE = "change_delivery_service_type"
    CLOSE_DELIVERY_ORDER = "close_delivery_order"
    PRINT_DELIVERY_BILL = "print_delivery_bill"
    PRINT_TABLE_ORDER_BILL = "print_table_order_bill"
    UPDATE_DELIVERY_ORDER_PROBLEM = "update_delivery_order_problem"
    UPDATE_DELIVERY_ORDER_STATUS = "update_delivery_order_status"
    UPDATE_DELIVERY_TRACKING_LINK = "update_delivery_tracking_link"

    # Deliveries (retrieve)
    GET_DELIVERIES_BY_DELIVERY_DATE_AND_PHONE = (
        "get_deliveries_by_delivery_date_and_phone"
    )
    GET_DELIVERIES_BY_DELIVERY_DATE_AND_STATUS = (
        "get_deliveries_by_delivery_date_and_status"
    )
    GET_DELIVERIES_BY_ID = "get_deliveries_by_id"
    GET_DELIVERIES_BY_REVISION = "get_deliveries_by_revision"
    GET_DELIVERY_HISTORY_BY_DELIVERY_DATE_AND_PHONE = (
        "get_delivery_history_by_delivery_date_and_phone"
    )
    SEARCH_DELIVERIES = "search_deliveries"

    # Delivery Restrictions
    GET_ALLOWED_DELIVERY_RESTRICTIONS = "get_allowed_delivery_restrictions"
    GET_DELIVERY_RESTRICTIONS = "get_delivery_restrictions"

    # Drafts
    CREATE_DELIVERY_DRAFT = "create_delivery_draft"
    SAVE_DELIVERY_DRAFT = "save_delivery_draft"
    COMMIT_DELIVERY_DRAFT = "commit_delivery_draft"
    DELETE_DELIVERY_DRAFT = "delete_delivery_draft"
    LOCK_DELIVERY_DRAFT = "lock_delivery_draft"
    UNLOCK_DELIVERY_DRAFT = "unlock_delivery_draft"
    GET_DELIVERY_DRAFT_BY_ID = "get_delivery_draft_by_id"
    GET_DELIVERY_DRAFTS_BY_FILTER = "get_delivery_drafts_by_filter"

    # Addresses
    GET_CITIES = "get_cities"
    GET_REGIONS = "get_regions"
    GET_STREETS_BY_CITY = "get_streets_by_city"
    GET_STREETS_BY_ID = "get_streets_by_id"

    # Discounts & Promotions
    CALCULATE_LOYALTY_CHECKIN = "calculate_loyalty_checkin"
    GET_COUPON_INFO = "get_coupon_info"
    GET_COUPON_SERIES = "get_coupon_series"
    GET_LOYALTY_MANUAL_CONDITIONS = "get_loyalty_manual_conditions"
    GET_LOYALTY_PROGRAMS = "get_loyalty_programs"
    GET_NON_ACTIVATED_COUPONS_BY_SERIES = "get_non_activated_coupons_by_series"

    # Marketing Sources
    GET_MARKETING_SOURCES = "get_marketing_sources"

    # Employees
    GET_COURIERS = "get_couriers"
    GET_COURIERS_BY_ROLE = "get_couriers_by_role"
    GET_EMPLOYEE_INFO = "get_employee_info"
    GET_ACTIVE_COURIER_LOCATIONS = "get_active_courier_locations"
    GET_ACTIVE_COURIER_LOCATIONS_BY_TERMINAL = (
        "get_active_courier_locations_by_terminal"
    )
    GET_COURIER_LOCATION_HISTORY = "get_courier_location_history"
    GET_PERSONAL_SESSION_INFO = "get_personal_session_info"
    GET_TERMINAL_GROUPS_OF_EMPLOYEE = "get_terminal_groups_of_employee"
    OPEN_PERSONAL_SESSION = "open_personal_session"
    CLOSE_PERSONAL_SESSION = "close_personal_session"

    # Messages
    CHECK_SMS_SENDING_POSSIBILITY = "check_sms_sending_possibility"
    CHECK_SMS_STATUS = "check_sms_status"
    SEND_LOYALTY_SMS = "send_loyalty_sms"
    SEND_LOYALTY_EMAIL = "send_loyalty_email"

    # Notifications
    SEND_NOTIFICATION = "send_notification"


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
    add_customer_magnet_card: RateLimitConfig
    remove_customer_magnet_card: RateLimitConfig
    add_customer_to_program: RateLimitConfig
    hold_customer_balance: RateLimitConfig
    cancel_customer_balance_hold: RateLimitConfig
    top_up_customer_balance: RateLimitConfig
    withdraw_customer_balance: RateLimitConfig
    get_loyalty_counters: RateLimitConfig
    get_customer_categories: RateLimitConfig
    add_customer_category: RateLimitConfig
    remove_customer_category: RateLimitConfig
    get_terminal_groups: RateLimitConfig
    check_terminal_groups_availability: RateLimitConfig
    get_external_menus: RateLimitConfig
    get_external_menu_by_id: RateLimitConfig
    get_stop_lists: RateLimitConfig
    add_products_to_stop_list: RateLimitConfig
    remove_products_from_stop_list: RateLimitConfig
    clear_stop_list: RateLimitConfig
    check_products_in_stop_list: RateLimitConfig
    get_nomenclature: RateLimitConfig
    get_combos_info: RateLimitConfig
    calculate_combo_price: RateLimitConfig
    get_cancel_causes: RateLimitConfig
    get_delivery_order_types: RateLimitConfig
    get_payment_types: RateLimitConfig
    get_discounts: RateLimitConfig
    get_removal_types: RateLimitConfig
    get_tips_types: RateLimitConfig
    create_delivery_order: RateLimitConfig
    add_delivery_order_items: RateLimitConfig
    add_delivery_order_payments: RateLimitConfig
    cancel_delivery_order: RateLimitConfig
    cancel_delivery_confirmation: RateLimitConfig
    confirm_delivery: RateLimitConfig
    change_delivery_comment: RateLimitConfig
    change_delivery_complete_before: RateLimitConfig
    change_delivery_driver_info: RateLimitConfig
    change_delivery_external_data: RateLimitConfig
    change_delivery_operator: RateLimitConfig
    change_delivery_payments: RateLimitConfig
    change_delivery_point: RateLimitConfig
    change_delivery_service_type: RateLimitConfig
    close_delivery_order: RateLimitConfig
    print_delivery_bill: RateLimitConfig
    print_table_order_bill: RateLimitConfig
    update_delivery_order_problem: RateLimitConfig
    update_delivery_order_status: RateLimitConfig
    update_delivery_tracking_link: RateLimitConfig
    get_deliveries_by_delivery_date_and_phone: RateLimitConfig
    get_deliveries_by_delivery_date_and_status: RateLimitConfig
    get_deliveries_by_id: RateLimitConfig
    get_deliveries_by_revision: RateLimitConfig
    get_delivery_history_by_delivery_date_and_phone: RateLimitConfig
    search_deliveries: RateLimitConfig
    get_allowed_delivery_restrictions: RateLimitConfig
    get_delivery_restrictions: RateLimitConfig
    create_delivery_draft: RateLimitConfig
    save_delivery_draft: RateLimitConfig
    commit_delivery_draft: RateLimitConfig
    delete_delivery_draft: RateLimitConfig
    lock_delivery_draft: RateLimitConfig
    unlock_delivery_draft: RateLimitConfig
    get_delivery_draft_by_id: RateLimitConfig
    get_delivery_drafts_by_filter: RateLimitConfig
    get_cities: RateLimitConfig
    get_regions: RateLimitConfig
    get_streets_by_city: RateLimitConfig
    get_streets_by_id: RateLimitConfig
    calculate_loyalty_checkin: RateLimitConfig
    get_coupon_info: RateLimitConfig
    get_coupon_series: RateLimitConfig
    get_loyalty_manual_conditions: RateLimitConfig
    get_loyalty_programs: RateLimitConfig
    get_non_activated_coupons_by_series: RateLimitConfig
    get_marketing_sources: RateLimitConfig
    get_couriers: RateLimitConfig
    get_couriers_by_role: RateLimitConfig
    get_employee_info: RateLimitConfig
    get_active_courier_locations: RateLimitConfig
    get_active_courier_locations_by_terminal: RateLimitConfig
    get_courier_location_history: RateLimitConfig
    get_personal_session_info: RateLimitConfig
    get_terminal_groups_of_employee: RateLimitConfig
    open_personal_session: RateLimitConfig
    close_personal_session: RateLimitConfig
    check_sms_sending_possibility: RateLimitConfig
    check_sms_status: RateLimitConfig
    send_loyalty_sms: RateLimitConfig
    send_loyalty_email: RateLimitConfig
    send_notification: RateLimitConfig

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
    _customer_categories_api: CustomerCategoriesApi | None
    _terminal_groups_api: TerminalGroupsApi | None
    _menu_api: MenuApi | None
    _dictionaries_api: DictionariesApi | None
    _deliveries_create_and_update_api: DeliveriesCreateAndUpdateApi | None
    _deliveries_retrieve_api: DeliveriesRetrieveApi | None
    _delivery_restrictions_api: DeliveryRestrictionsApi | None
    _drafts_api: DraftsApi | None
    _addresses_api: AddressesApi | None
    _discounts_and_promotions_api: DiscountsAndPromotionsApi | None
    _marketing_sources_api: MarketingSourcesApi | None
    _employees_api: EmployeesApi | None
    _messages_api: MessagesApi | None
    _notifications_api: NotificationsApi | None

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

    async def get_customer_categories_api(self) -> CustomerCategoriesApi:
        """Получить клиент CustomerCategoriesApi."""
        await self._ensure_token_manager()
        if self._customer_categories_api is None:
            self._customer_categories_api = CustomerCategoriesApi(
                api_client=self._api_client
            )
        return self._customer_categories_api

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

    async def get_deliveries_create_and_update_api(
        self,
    ) -> DeliveriesCreateAndUpdateApi:
        """Получить клиент DeliveriesCreateAndUpdateApi."""
        await self._ensure_token_manager()
        if self._deliveries_create_and_update_api is None:
            self._deliveries_create_and_update_api = DeliveriesCreateAndUpdateApi(
                api_client=self._api_client
            )
        return self._deliveries_create_and_update_api

    async def get_deliveries_retrieve_api(self) -> DeliveriesRetrieveApi:
        """Получить клиент DeliveriesRetrieveApi."""
        await self._ensure_token_manager()
        if self._deliveries_retrieve_api is None:
            self._deliveries_retrieve_api = DeliveriesRetrieveApi(
                api_client=self._api_client
            )
        return self._deliveries_retrieve_api

    async def get_delivery_restrictions_api(self) -> DeliveryRestrictionsApi:
        """Получить клиент DeliveryRestrictionsApi."""
        await self._ensure_token_manager()
        if self._delivery_restrictions_api is None:
            self._delivery_restrictions_api = DeliveryRestrictionsApi(
                api_client=self._api_client
            )
        return self._delivery_restrictions_api

    async def get_drafts_api(self) -> DraftsApi:
        """Получить клиент DraftsApi."""
        await self._ensure_token_manager()
        if self._drafts_api is None:
            self._drafts_api = DraftsApi(api_client=self._api_client)
        return self._drafts_api

    async def get_addresses_api(self) -> AddressesApi:
        """Получить клиент AddressesApi."""
        await self._ensure_token_manager()
        if self._addresses_api is None:
            self._addresses_api = AddressesApi(api_client=self._api_client)
        return self._addresses_api

    async def get_discounts_and_promotions_api(self) -> DiscountsAndPromotionsApi:
        """Получить клиент DiscountsAndPromotionsApi."""
        await self._ensure_token_manager()
        if self._discounts_and_promotions_api is None:
            self._discounts_and_promotions_api = DiscountsAndPromotionsApi(
                api_client=self._api_client
            )
        return self._discounts_and_promotions_api

    async def get_marketing_sources_api(self) -> MarketingSourcesApi:
        """Получить клиент MarketingSourcesApi."""
        await self._ensure_token_manager()
        if self._marketing_sources_api is None:
            self._marketing_sources_api = MarketingSourcesApi(
                api_client=self._api_client
            )
        return self._marketing_sources_api

    async def get_employees_api(self) -> EmployeesApi:
        """Получить клиент EmployeesApi."""
        await self._ensure_token_manager()
        if self._employees_api is None:
            self._employees_api = EmployeesApi(api_client=self._api_client)
        return self._employees_api

    async def get_messages_api(self) -> MessagesApi:
        """Получить клиент MessagesApi."""
        await self._ensure_token_manager()
        if self._messages_api is None:
            self._messages_api = MessagesApi(api_client=self._api_client)
        return self._messages_api

    async def get_notifications_api(self) -> NotificationsApi:
        """Получить клиент NotificationsApi."""
        await self._ensure_token_manager()
        if self._notifications_api is None:
            self._notifications_api = NotificationsApi(api_client=self._api_client)
        return self._notifications_api

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
