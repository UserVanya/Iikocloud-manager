"""Исключения для работы с iikocloud API.

Минимальный набор исключений для обработки ошибок аутентификации.
Все остальные ошибки API пробрасываются из iikocloud_client напрямую.
"""


class IikoCloudException(Exception):
    """Базовое исключение для ошибок iikocloud API."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class IikoCloudAuthException(IikoCloudException):
    """Исключение при ошибках аутентификации.

    Выбрасывается при:
    - Некорректном API-ключе (401 на запрос токена)
    - Ошибках получения/обновления токена
    """
