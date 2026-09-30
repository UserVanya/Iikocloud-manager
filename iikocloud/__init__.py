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
from iikocloud.exceptions import IikoCloudAuthException, IikoCloudException, MenuTooEarly
from iikocloud.menu_windows import MenuWindows
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
    "MenuTooEarly",
    # Menu windows (0.3.0)
    "MenuWindows",
    # Rate Limiting
    "GlobalRateLimiter",
    "RateLimitConfig",
    "TokenBucketRateLimiter",
    # Token Management
    "TokenManager",
]
