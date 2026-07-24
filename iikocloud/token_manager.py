"""Менеджер токенов для iikocloud API (auth v2).

Управляет получением и обновлением Bearer-токенов через authenticate_v2.
Токен обновляется только при получении 401 ошибки (с dedup по token_version).
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from iikocloud_client import ApiClient, AuthorizationApi, GetAccessTokenV2Request
from iikocloud_client.exceptions import UnauthorizedException

from iikocloud.exceptions import IikoCloudAuthException

logger = logging.getLogger(__name__)


class TokenManager:
    """Менеджер токенов для конкретного ApiClient.

    Токен запрашивается/обновляется только при 401 ошибке.
    Если обновление уже идёт — другие корутины ждут через Event.
    Rate limiting передаётся снаружи (глобальный + auth).
    """

    _instances: dict[str, "TokenManager"] = {}
    _global_lock: asyncio.Lock | None = None

    def __init__(
        self,
        api_client: ApiClient,
        api_key: str,
        app_id: str,
        client_secret: str,
        key_id: str,
    ) -> None:
        """Инициализация менеджера токенов.

        Args:
            api_client: Клиент API для установки токена
            api_key: API-ключ (auth v2)
            app_id: Идентификатор приложения (UUID)
            client_secret: Секрет клиента (auth v2)
            key_id: Уникальный идентификатор ключа (multitone)
        """
        self._api_client = api_client
        self._api_key = api_key
        self._app_id = app_id
        self._client_secret = client_secret
        self._key_id = key_id
        self._token: str | None = None
        self._token_version: int = 0
        self._authorization_api = AuthorizationApi(api_client=self._api_client)
        self._lock = asyncio.Lock()
        self._refresh_event = asyncio.Event()
        self._refresh_event.set()

    @property
    def token_version(self) -> int:
        """Текущая версия токена (увеличивается при каждом успешном fetch)."""
        return self._token_version

    @classmethod
    async def get_instance(
        cls,
        api_client: ApiClient,
        api_key: str,
        app_id: str,
        client_secret: str,
        key_id: str,
    ) -> "TokenManager":
        """Получить или создать экземпляр для данного key_id.

        Args:
            api_client: Клиент API
            api_key: API-ключ (auth v2)
            app_id: Идентификатор приложения (UUID)
            client_secret: Секрет клиента (auth v2)
            key_id: Уникальный идентификатор ключа

        Returns:
            Экземпляр TokenManager
        """
        if cls._global_lock is None:
            cls._global_lock = asyncio.Lock()

        async with cls._global_lock:
            if key_id not in cls._instances:
                cls._instances[key_id] = cls(
                    api_client, api_key, app_id, client_secret, key_id
                )
            return cls._instances[key_id]

    async def _fetch_token(
        self,
        acquire_global: Callable[[], Awaitable[None]],
        acquire_auth: Callable[[], Awaitable[None]],
    ) -> str:
        """Получить новый токен от API через authenticate_v2.

        Args:
            acquire_global: Функция получения глобального rate limit токена
            acquire_auth: Функция получения auth rate limit токена

        Returns:
            Новый токен

        Raises:
            IikoCloudAuthException: При ошибке получения токена
        """
        await acquire_global()
        await acquire_auth()

        # Токен НЕ сбрасывается перед запросом: authenticate_v2 не использует
        # auth_settings (Bearer туда не уходит), а configuration разделяется
        # со всеми параллельными запросами этого ApiClient — обнуление здесь
        # заставило бы их уйти без Authorization и получить 401.
        try:
            request = GetAccessTokenV2Request(
                api_key=self._api_key,
                app_id=self._app_id,
                client_secret=self._client_secret,
            )
            logger.debug("Запрос токена для key_id=%s", self._key_id)
            response = await self._authorization_api.authenticate_v2(
                get_access_token_v2_request=request
            )
            return response.token
        except UnauthorizedException as exc:
            # 401 на auth запрос = некорректные credentials
            logger.error(
                "Некорректные credentials для key_id=%s: получен 401 на запрос авторизации",
                self._key_id,
            )
            raise IikoCloudAuthException(
                "Некорректные credentials: получен 401 на запрос авторизации",
                original_error=exc,
            ) from exc
        except Exception as exc:
            logger.error(
                "Ошибка при получении токена для key_id=%s: %s",
                self._key_id,
                exc,
            )
            raise IikoCloudAuthException(
                f"Ошибка при получении токена: {exc}", original_error=exc
            ) from exc

    async def ensure_token_with_limits(
        self,
        acquire_global: Callable[[], Awaitable[None]],
        acquire_auth: Callable[[], Awaitable[None]],
    ) -> None:
        """Получить токен, если его ещё нет.

        Args:
            acquire_global: Функция получения глобального rate limit токена
            acquire_auth: Функция получения auth rate limit токена
        """
        if self._token is not None:
            return

        async with self._lock:
            # Double-check после получения lock
            if self._token is not None:
                return

            self._refresh_event.clear()
            try:
                self._token = await self._fetch_token(acquire_global, acquire_auth)
                self._token_version += 1
                self._api_client.configuration.access_token = self._token
                logger.info(
                    "Токен получен успешно для key_id=%s (версия: %d)",
                    self._key_id,
                    self._token_version,
                )
            finally:
                self._refresh_event.set()

    async def refresh_token_if_401(
        self,
        error: Exception,
        acquire_global: Callable[[], Awaitable[None]],
        acquire_auth: Callable[[], Awaitable[None]],
        version_before: int | None = None,
    ) -> bool:
        """Обновить токен при 401 ошибке (dedup по token_version).

        Args:
            error: Исключение, которое может быть 401
            acquire_global: Функция получения глобального rate limit токена
            acquire_auth: Функция получения auth rate limit токена
            version_before: Версия токена до неудачного запроса;
                если уже изменилась — refresh пропускается

        Returns:
            True если токен был обновлён (или уже обновлён другим),
            False если ошибка не 401 или параллельный refresh не сдвинул версию

        Raises:
            IikoCloudAuthException: При ошибке обновления токена
        """
        error_status = getattr(error, "status", None)
        is_401 = isinstance(error, UnauthorizedException) or error_status == 401
        if not is_401:
            logger.debug("Не 401 ошибка, пропускаем обновление токена")
            return False

        if version_before is None:
            version_before = self._token_version

        logger.debug("Получена 401 ошибка, версия токена: %d", version_before)

        # Быстрый путь: кто-то уже обновил токен после нашего запроса
        if self._token_version != version_before:
            logger.debug(
                "Токен уже обновлён другой корутиной: %d -> %d",
                version_before,
                self._token_version,
            )
            return True

        # Если кто-то уже обновляет — ждём и проверяем, что версия реально сдвинулась
        if not self._refresh_event.is_set():
            logger.debug("Другая корутина обновляет токен, ожидаем...")
            await self._refresh_event.wait()
            return self._token_version != version_before

        async with self._lock:
            # Проверяем, не обновил ли кто-то токен пока мы ждали lock
            if self._token_version != version_before:
                logger.debug(
                    "Токен уже обновлён другой корутиной: %d -> %d",
                    version_before,
                    self._token_version,
                )
                return True

            self._refresh_event.clear()
            try:
                self._token = await self._fetch_token(acquire_global, acquire_auth)
                self._token_version += 1
                self._api_client.configuration.access_token = self._token
                logger.info(
                    "Токен обновлён после 401 для key_id=%s (версия: %d)",
                    self._key_id,
                    self._token_version,
                )
            except Exception as exc:
                logger.error(
                    "Ошибка при обновлении токена для key_id=%s: %s",
                    self._key_id,
                    exc,
                )
                self._token = None
                self._api_client.configuration.access_token = None
                raise
            finally:
                self._refresh_event.set()

        return True

    @classmethod
    async def close_all(cls) -> None:
        """Сбросить все экземпляры (для тестов)."""
        cls._instances.clear()
        cls._global_lock = None
