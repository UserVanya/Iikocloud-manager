"""Модуль для работы с iikocloud API.

Предоставляет клиента с автоматическим управлением токенами,
rate limiting и retry при 401 ошибках.

Пример использования:
    from iikocloud import get_iikocloud_config, IikoCloudApiClientManager

    config = get_iikocloud_config()
    manager = await IikoCloudApiClientManager.from_config(config)
    orgs = await manager.get_organizations(request)
"""

from iikocloud.api_client_manager import (
    ApiCredentials,
    ApiMethod,
    IikoCloudApiClientManager,
    MethodRateLimits,
)
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
    IikoCloudConnectionException,
    IikoCloudCustomerNotFoundException,
    IikoCloudException,
    IikoCloudRateLimitException,
    IikoCloudTimeoutException,
    IikoCloudValidationException,
)
from iikocloud.rate_limiter import (
    GlobalRateLimiter,
    RateLimitConfig,
    TokenBucketRateLimiter,
)
from iikocloud.token_manager import TokenManager

__all__ = [
    # API Client Manager
    "ApiCredentials",
    "ApiMethod",
    "IikoCloudApiClientManager",
    "MethodRateLimits",
    # Configuration
    "IikoCloudConfig",
    "MethodRateLimitsSettings",
    "RateLimitSettings",
    "get_config",
    "get_iikocloud_config",
    "parse_config_file",
    # Exceptions
    "IikoCloudAuthException",
    "IikoCloudConnectionException",
    "IikoCloudCustomerNotFoundException",
    "IikoCloudException",
    "IikoCloudRateLimitException",
    "IikoCloudTimeoutException",
    "IikoCloudValidationException",
    # Rate Limiting
    "GlobalRateLimiter",
    "RateLimitConfig",
    "TokenBucketRateLimiter",
    # Token Management
    "TokenManager",
]
