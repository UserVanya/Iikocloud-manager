"""Тесты для exceptions модуля."""

import pytest

from iikocloud.exceptions import (
    IikoCloudAuthException,
    IikoCloudException,
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


class TestIikoCloudAuthException:
    """Тесты для исключения аутентификации."""

    def test_inherits_from_base(self) -> None:
        """IikoCloudAuthException наследуется от IikoCloudException."""
        exc = IikoCloudAuthException("Auth failed")

        assert isinstance(exc, IikoCloudException)
        assert isinstance(exc, Exception)

    def test_catch_by_base_class(self) -> None:
        """IikoCloudAuthException ловится базовым классом."""
        with pytest.raises(IikoCloudException):
            raise IikoCloudAuthException("Auth failed")

    def test_catch_specific(self) -> None:
        """IikoCloudAuthException можно поймать отдельно."""
        with pytest.raises(IikoCloudAuthException):
            raise IikoCloudAuthException("Auth failed")

    def test_with_original_error(self) -> None:
        """IikoCloudAuthException сохраняет оригинальную ошибку."""
        original = ConnectionError("Connection refused")
        exc = IikoCloudAuthException("Auth failed", original_error=original)

        assert exc.original_error is original
        assert str(exc) == "Auth failed"
