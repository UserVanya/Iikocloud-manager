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
    get_organizations_settings: RateLimitSettings = RateLimitSettings(
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

    # Terminal Groups
    get_terminal_groups: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )
    check_terminal_groups_alive: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Menu
    get_external_menus: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=1800.0
    )
    get_menu_by_id: RateLimitSettings = RateLimitSettings(
        max_requests=5, time_window_seconds=60.0
    )
    get_stop_lists: RateLimitSettings = RateLimitSettings(
        max_requests=10, time_window_seconds=60.0
    )

    # Dictionaries
    get_delivery_cancel_causes: RateLimitSettings = RateLimitSettings(
        max_requests=1, time_window_seconds=60.0
    )
    get_order_types: RateLimitSettings = RateLimitSettings(
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

    def compute_global_limit(self) -> RateLimitSettings:
        """Вычислить глобальный лимит как самый свободный из всех методов.

        Самый свободный = максимальный rate (requests per second).

        Returns:
            RateLimitSettings с самым свободным лимитом
        """
        all_limits = [
            self.auth,
            self.get_organizations,
            self.get_organizations_settings,
            self.create_or_update_customer,
            self.get_customer_info,
            self.delete_customers,
            self.restore_customers,
            self.get_terminal_groups,
            self.check_terminal_groups_alive,
            self.get_external_menus,
            self.get_menu_by_id,
            self.get_stop_lists,
            self.get_delivery_cancel_causes,
            self.get_order_types,
            self.get_payment_types,
            self.get_discounts,
            self.get_removal_types,
        ]

        # Находим метод с максимальным rate (requests/second)
        max_rate = 0.0
        best_limit = all_limits[0]

        for limit in all_limits:
            rate = limit.max_requests / limit.time_window_seconds
            if rate > max_rate:
                max_rate = rate
                best_limit = limit

        return best_limit


class IikoCloudConfig(BaseModel):
    """Конфигурация для подключения к iikocloud API."""

    # API логин для получения токена
    api_login: SecretStr

    # Уникальный идентификатор ключа (для multitone паттерна)
    key_id: str

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
