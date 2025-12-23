"""Исключения для работы с iikocloud API."""


class IikoCloudException(Exception):
    """Базовое исключение для ошибок iikocloud API."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


class IikoCloudAuthException(IikoCloudException):
    """Исключение при ошибках аутентификации."""


class IikoCloudConnectionException(IikoCloudException):
    """Исключение при проблемах с подключением к iikocloud API."""


class IikoCloudTimeoutException(IikoCloudException):
    """Исключение при таймауте запроса к iikocloud API."""


class IikoCloudCustomerNotFoundException(IikoCloudException):
    """Исключение когда клиент не найден в iikocloud."""


class IikoCloudValidationException(IikoCloudException):
    """Исключение при ошибках валидации данных для iikocloud API."""


class IikoCloudRateLimitException(IikoCloudException):
    """Исключение при превышении лимита запросов."""
