"""Тесты для exceptions модуля."""

import pytest

from iikocloud.exceptions import (
    IikoCloudAuthException,
    IikoCloudConnectionException,
    IikoCloudCustomerNotFoundException,
    IikoCloudException,
    IikoCloudRateLimitException,
    IikoCloudTimeoutException,
    IikoCloudValidationException,
)

# Маркируем все тесты в этом модуле как unit-тесты
pytestmark = pytest.mark.unit


class TestIikoCloudException:
    """Тесты для базового исключения."""

    def test_message(self) -> None:
        """Сообщение сохраняется корректно."""
        exc = IikoCloudException("Test error")

        assert str(exc) == "Test error"

    def test_original_error(self) -> None:
        """Оригинальная ошибка сохраняется."""
        original = ValueError("Original error")
        exc = IikoCloudException("Wrapped error", original_error=original)

        assert exc.original_error is original

    def test_original_error_default_none(self) -> None:
        """По умолчанию original_error = None."""
        exc = IikoCloudException("Error")

        assert exc.original_error is None


class TestExceptionHierarchy:
    """Тесты иерархии исключений."""

    @pytest.mark.parametrize(
        "exception_class",
        [
            IikoCloudAuthException,
            IikoCloudConnectionException,
            IikoCloudTimeoutException,
            IikoCloudCustomerNotFoundException,
            IikoCloudValidationException,
            IikoCloudRateLimitException,
        ],
    )
    def test_inherits_from_base(
        self, exception_class: type[IikoCloudException]
    ) -> None:
        """Все исключения наследуются от IikoCloudException."""
        exc = exception_class("Test")

        assert isinstance(exc, IikoCloudException)
        assert isinstance(exc, Exception)

    def test_catch_by_base_class(self) -> None:
        """Специфичные исключения ловятся базовым классом."""
        with pytest.raises(IikoCloudException):
            raise IikoCloudAuthException("Auth failed")

    def test_catch_specific_exception(self) -> None:
        """Специфичные исключения можно ловить отдельно."""
        with pytest.raises(IikoCloudAuthException):
            raise IikoCloudAuthException("Auth failed")

        # Но не другие типы
        with pytest.raises(IikoCloudConnectionException):
            raise IikoCloudConnectionException("Connection failed")

