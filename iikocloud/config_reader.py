"""Конфигурация для iikocloud API клиента.

Читает настройки из YAML-файла, путь к которому указывается
в переменной окружения IIKOCLOUD_CONFIG.

Переменные окружения автоматически загружаются из .env файла.
"""

from functools import lru_cache
from os import getenv
from typing import Any, TypeVar, cast

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr, field_validator
from yaml import CSafeLoader as SafeLoader
from yaml import load

# Автоматически загружаем переменные из .env файла
load_dotenv()

ConfigType = TypeVar("ConfigType", bound=BaseModel)


class RateLimitSettings(BaseModel):
    """Настройки rate limiting для одного метода API."""

    max_requests: int
    time_window_seconds: float

    @field_validator("max_requests")
    @classmethod
    def validate_max_requests(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_requests должен быть >= 1")
        return v

    @field_validator("time_window_seconds")
    @classmethod
    def validate_time_window(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("time_window_seconds должен быть > 0")
        return v


class MethodRateLimitsSettings(BaseModel):
    """Настройки rate limiting для каждого метода API.

    Глобальный лимит автоматически вычисляется как самый свободный
    (максимальный requests/time_window) из всех методов.
    """

    # Авторизация
    auth: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=5.0
    )

    # Organizations
    get_organizations: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=10.0
    )
    get_organization_settings: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=10.0
    )

    # Customers
    create_or_update_customer: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    get_customer_info: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    delete_customers: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    restore_customers: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )

    # Customers — cards / programs / wallets
    add_customer_magnet_card: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    remove_customer_magnet_card: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    add_customer_to_program: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    hold_customer_balance: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    cancel_customer_balance_hold: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    top_up_customer_balance: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    withdraw_customer_balance: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    get_loyalty_counters: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Customer Categories
    get_customer_categories: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    add_customer_category: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    remove_customer_category: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )

    # Terminal Groups
    get_terminal_groups: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    check_terminal_groups_availability: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Menu
    get_external_menus: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=1800.0
    )
    get_external_menu_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=5, time_window_seconds=60.0
    )
    get_stop_lists: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Menu — stop lists / nomenclature / combos
    add_products_to_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    remove_products_from_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    clear_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    check_products_in_stop_list: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_nomenclature: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_combos_info: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    calculate_combo_price: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Dictionaries
    get_cancel_causes: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_delivery_order_types: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_payment_types: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_discounts: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_removal_types: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_tips_types: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )

    # Deliveries (create & update)
    create_delivery_order: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    add_delivery_order_items: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    add_delivery_order_payments: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    cancel_delivery_order: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    cancel_delivery_confirmation: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    confirm_delivery: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_comment: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_complete_before: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_driver_info: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_external_data: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_operator: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_payments: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_point: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_delivery_service_type: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    close_delivery_order: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    print_delivery_bill: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    print_table_order_bill: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    update_delivery_order_problem: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    update_delivery_order_status: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    update_delivery_tracking_link: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )

    # Deliveries (retrieve)
    get_deliveries_by_delivery_date_and_phone: RateLimitSettings = (
        RateLimitSettings(max_requests=10, time_window_seconds=60.0)
    )
    get_deliveries_by_delivery_date_and_status: RateLimitSettings = (
        RateLimitSettings(max_requests=10, time_window_seconds=60.0)
    )
    get_deliveries_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_deliveries_by_revision: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_delivery_history_by_delivery_date_and_phone: RateLimitSettings = (
        RateLimitSettings(max_requests=10, time_window_seconds=60.0)
    )
    search_deliveries: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Delivery Restrictions
    get_allowed_delivery_restrictions: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    get_delivery_restrictions: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )

    # Drafts
    create_delivery_draft: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    save_delivery_draft: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    commit_delivery_draft: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    delete_delivery_draft: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    lock_delivery_draft: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    unlock_delivery_draft: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    get_delivery_draft_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    get_delivery_drafts_by_filter: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )

    # Addresses
    get_cities: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_regions: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_streets_by_city: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_streets_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )

    # Discounts & Promotions
    calculate_loyalty_checkin: RateLimitSettings = RateLimitSettings(
        max_requests=1000, time_window_seconds=60.0
    )
    get_coupon_info: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_coupon_series: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_loyalty_manual_conditions: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_loyalty_programs: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_non_activated_coupons_by_series: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Marketing Sources
    get_marketing_sources: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )

    # Employees
    get_couriers: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_couriers_by_role: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_employee_info: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_active_courier_locations: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_active_courier_locations_by_terminal: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_courier_location_history: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_personal_session_info: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_terminal_groups_of_employee: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    open_personal_session: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    close_personal_session: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )

    # Messages
    check_sms_sending_possibility: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    check_sms_status: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    send_loyalty_sms: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    send_loyalty_email: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )

    # Notifications
    send_notification: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )

    # Operations (polling-метод)
    get_command_status: RateLimitSettings = RateLimitSettings(
        max_requests=60, time_window_seconds=60.0
    )

    # Report
    get_customer_transactions_by_date: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    get_customer_transactions_by_revision: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Webhooks
    get_webhook_settings: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    update_webhook_settings: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )

    # Banquets & Reserves
    get_reserve_available_organizations: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    get_reserve_terminal_groups: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    get_reserve_restaurant_sections: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    get_reserve_statuses_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    get_restaurant_sections_workload: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    create_reserve: RateLimitSettings = RateLimitSettings(
        max_requests=20, time_window_seconds=60.0
    )
    add_banquet_order_items: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    add_banquet_order_payments: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    cancel_reserve: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_banquet_order_items: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_reserve_estimated_start_time: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )
    change_reserve_tables: RateLimitSettings = RateLimitSettings(
        max_requests=100, time_window_seconds=60.0
    )

    def compute_global_limit(self) -> RateLimitSettings:
        """Вычислить глобальный лимит как самый свободный из всех методов.

        Самый свободный = максимальный rate (requests per second).
        Перебираются все поля модели, поэтому новый метод не нужно
        добавлять в отдельный список вручную.

        Returns:
            RateLimitSettings с самым свободным лимитом
        """
        limits = (
            cast(RateLimitSettings, getattr(self, name))
            for name in type(self).model_fields
        )
        return max(limits, key=lambda s: s.max_requests / s.time_window_seconds)


class IikoCloudConfig(BaseModel):
    """Конфигурация для подключения к iikocloud API."""

    api_key: SecretStr
    app_id: str
    client_secret: SecretStr

    # Rate limits для каждого метода API
    rate_limits: MethodRateLimitsSettings = MethodRateLimitsSettings()


@lru_cache
def parse_config_file() -> dict[str, Any]:
    """Прочитать и распарсить YAML-файл конфигурации.

    Путь к файлу берётся из переменной окружения IIKOCLOUD_CONFIG.

    Returns:
        Словарь с конфигурацией

    Raises:
        ValueError: Если переменная окружения не задана
        FileNotFoundError: Если файл не найден
    """
    file_path = getenv("IIKOCLOUD_CONFIG")
    if file_path is None:
        raise ValueError(
            "Переменная окружения IIKOCLOUD_CONFIG не задана. "
            "Укажите путь к файлу конфигурации."
        )

    with open(file_path, "rb") as file:
        config_data = load(file, Loader=SafeLoader)

    if not isinstance(config_data, dict):
        raise ValueError("Конфигурация должна быть словарём")
    return config_data


@lru_cache
def get_config(model: type[ConfigType], root_key: str) -> ConfigType:  # noqa: UP047
    """Получить конфигурацию определённого типа из файла.

    Args:
        model: Pydantic-модель для валидации
        root_key: Корневой ключ в YAML-файле

    Returns:
        Экземпляр модели с заполненными значениями

    Raises:
        ValueError: Если ключ не найден в конфигурации
    """
    config_dict = parse_config_file()
    if root_key not in config_dict:
        raise ValueError(f"Ключ '{root_key}' не найден в конфигурации")
    return model.model_validate(config_dict[root_key])


def get_iikocloud_config() -> IikoCloudConfig:
    """Получить конфигурацию iikocloud.

    Удобная обёртка для получения IikoCloudConfig.

    Returns:
        Экземпляр IikoCloudConfig
    """
    return cast(IikoCloudConfig, get_config(IikoCloudConfig, "iikocloud"))


def clear_config_cache() -> None:
    """Сбросить кэш конфигурации (для тестов)."""
    parse_config_file.cache_clear()
    get_config.cache_clear()
