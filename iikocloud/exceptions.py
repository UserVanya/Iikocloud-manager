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


#: Чем занято окно меню — словами для журнала и для вызывающего.
MENU_WAIT_WORDS = {
    "key": "окно чтения меню ключа",
    "organization": "окно чтения меню организации",
    "paused": "пауза чтения меню ключа после «слишком часто» от iiko",
}


class MenuTooEarly(IikoCloudException):
    """Меню читать пока рано — окно ключа, окно организации или пауза после 429
    (выпуск 0.3.0).

    Не ожидание, а ответ: ``seconds`` — через сколько можно, ``reason`` — ``key``,
    ``organization`` или ``paused``.
    """

    def __init__(self, seconds: int, reason: str) -> None:
        super().__init__(
            f"{MENU_WAIT_WORDS.get(reason, reason)}; следующее — через {seconds} с"
        )
        self.seconds = seconds
        self.reason = reason


class MenuAnswerUnreadable(IikoCloudException):
    """iiko ответил на чтение меню успехом (2xx), но тело в меню V3 не разобрано
    (выпуск 0.4.0).

    ``raw`` — тело ответа байт в байт, ``content_type`` — его заголовок Content-Type
    (``None``, если iiko его не прислал). Причина — в ``original_error`` и ``__cause__``:
    обычно ``ValidationError`` модели, реже неверный JSON.
    """

    def __init__(
        self,
        raw: bytes,
        content_type: str | None,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(
            f"ответ iiko на меню не разобран: {len(raw)} байт, "
            f"тип содержимого — {content_type or 'не указан'}",
            original_error,
        )
        self.raw = raw
        self.content_type = content_type
