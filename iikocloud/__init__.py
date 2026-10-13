"""Модуль для работы с iikocloud API."""

from iikocloud.api_client_manager import (
    ApiCredentials,
    ApiMethod,
    IikoCloudApiClientManager,
    MethodRateLimits,
)
from iikocloud.config_reader import (
    IikoCloudConfig,
    MenuWindowsSettings,
    MethodRateLimitsSettings,
    RateLimitSettings,
    clear_config_cache,
    get_config,
    get_iikocloud_config,
    parse_config_file,
)
from iikocloud.exceptions import (
    IikoCloudAuthException,
    IikoCloudException,
    MenuAnswerUnreadable,
    MenuTooEarly,
)
from iikocloud.menu_windows import MenuWindows
from iikocloud.mixins.employees.helpers import EMPLOYEE_CONTACT_FIELDS
from iikocloud.mixins.menu.answer import MenuV3Answer
from iikocloud.rate_limiter import (
    GlobalRateLimiter,
    RateLimitConfig,
    TokenBucketRateLimiter,
)
from iikocloud.token_manager import TokenManager

__all__ = [
    # API Client
    "ApiCredentials",
    "ApiMethod",
    "IikoCloudApiClientManager",
    "MethodRateLimits",
    # Configuration
    "IikoCloudConfig",
    "MenuWindowsSettings",
    "MethodRateLimitsSettings",
    "RateLimitSettings",
    "clear_config_cache",
    "get_config",
    "get_iikocloud_config",
    "parse_config_file",
    # Exceptions
    "IikoCloudAuthException",
    "IikoCloudException",
    "MenuAnswerUnreadable",
    "MenuTooEarly",
    # Menu windows (0.3.0)
    "MenuWindows",
    # Menu with the raw iiko answer (0.4.0)
    "MenuV3Answer",
    # Employees: card fields with the phone for list_all_employees (0.5.0)
    "EMPLOYEE_CONTACT_FIELDS",
    # Rate Limiting
    "GlobalRateLimiter",
    "RateLimitConfig",
    "TokenBucketRateLimiter",
    # Token Management
    "TokenManager",
]
