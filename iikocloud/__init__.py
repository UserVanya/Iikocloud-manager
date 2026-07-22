"""Модуль для работы с iikocloud API.

Task 10 restores full package exports (ApiClientManager, TokenManager, etc.).
Until then, only submodules that do not pull broken SDK symbols are re-exported.
"""

from iikocloud.config_reader import (
    IikoCloudConfig,
    MethodRateLimitsSettings,
    RateLimitSettings,
    get_config,
    get_iikocloud_config,
    parse_config_file,
)
from iikocloud.exceptions import (
    IikoCloudAuthException,
    IikoCloudException,
)
from iikocloud.rate_limiter import (
    GlobalRateLimiter,
    RateLimitConfig,
    TokenBucketRateLimiter,
)

__all__ = [
    # Configuration
    "IikoCloudConfig",
    "MethodRateLimitsSettings",
    "RateLimitSettings",
    "get_config",
    "get_iikocloud_config",
    "parse_config_file",
    # Exceptions
    "IikoCloudAuthException",
    "IikoCloudException",
    # Rate Limiting
    "GlobalRateLimiter",
    "RateLimitConfig",
    "TokenBucketRateLimiter",
]
