"""Тесты для config_reader модуля."""

import os
import tempfile

import pytest

from iikocloud.config_reader import (
    IikoCloudConfig,
    MethodRateLimitsSettings,
    RateLimitSettings,
    get_config,
    get_iikocloud_config,
    parse_config_file,
)

# Маркируем все тесты в этом модуле как unit-тесты
pytestmark = pytest.mark.unit


# Очищаем кэш между тестами
@pytest.fixture(autouse=True)
def clear_cache() -> None:
    """Очистить кэш lru_cache перед каждым тестом."""
    parse_config_file.cache_clear()
    get_config.cache_clear()


class TestRateLimitSettings:
    """Тесты для RateLimitSettings."""

    def test_valid_settings(self) -> None:
        """Валидные настройки создаются корректно."""
        settings = RateLimitSettings(max_requests=10, time_window_seconds=1.0)

        assert settings.max_requests == 10
        assert settings.time_window_seconds == 1.0

    def test_invalid_max_requests(self) -> None:
        """max_requests < 1 вызывает ошибку."""
        with pytest.raises(ValueError, match="max_requests должен быть >= 1"):
            RateLimitSettings(max_requests=0, time_window_seconds=1.0)

    def test_invalid_time_window(self) -> None:
        """time_window_seconds <= 0 вызывает ошибку."""
        with pytest.raises(ValueError, match="time_window_seconds должен быть > 0"):
            RateLimitSettings(max_requests=1, time_window_seconds=0)


class TestMethodRateLimitsSettings:
    """Тесты для MethodRateLimitsSettings."""

    def test_default_values(self) -> None:
        """Дефолтные значения устанавливаются корректно."""
        settings = MethodRateLimitsSettings()

        assert settings.auth.max_requests == 1
        assert settings.auth.time_window_seconds == 5.0
        assert settings.create_or_update_customer.max_requests == 100
        assert settings.get_external_menus.time_window_seconds == 1800.0

    def test_compute_global_limit(self) -> None:
        """compute_global_limit возвращает самый свободный лимит."""
        settings = MethodRateLimitsSettings()
        global_limit = settings.compute_global_limit()

        # Самый свободный лимит = максимальный rate
        # customers: 100/60 = 1.67 rps - это максимальный rate
        assert global_limit.max_requests == 100
        assert global_limit.time_window_seconds == 60.0


class TestIikoCloudConfig:
    """Тесты для IikoCloudConfig."""

    def test_valid_config(self) -> None:
        """Валидная конфигурация создаётся корректно."""
        config = IikoCloudConfig(
            api_login="test-login",
            key_id="test-key",
        )

        assert config.api_login.get_secret_value() == "test-login"
        assert config.key_id == "test-key"

    def test_secret_str_hidden(self) -> None:
        """api_login скрывается при преобразовании в строку."""
        config = IikoCloudConfig(
            api_login="secret-login",
            key_id="test-key",
        )

        # SecretStr должен скрывать значение
        assert "secret-login" not in str(config)


class TestParseConfigFile:
    """Тесты для parse_config_file."""

    def test_missing_env_variable(self) -> None:
        """Отсутствие переменной окружения вызывает ошибку."""
        # Удаляем переменную если есть
        os.environ.pop("IIKOCLOUD_CONFIG", None)

        with pytest.raises(ValueError, match="IIKOCLOUD_CONFIG не задана"):
            parse_config_file()

    def test_valid_yaml_file(self) -> None:
        """Валидный YAML файл парсится корректно."""
        yaml_content = """
iikocloud:
  api_login: "test-login"
  key_id: "test"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            os.environ["IIKOCLOUD_CONFIG"] = f.name

            try:
                result = parse_config_file()
                assert "iikocloud" in result
                assert result["iikocloud"]["api_login"] == "test-login"
            finally:
                os.environ.pop("IIKOCLOUD_CONFIG", None)
                os.unlink(f.name)


class TestGetConfig:
    """Тесты для get_config."""

    def test_missing_root_key(self) -> None:
        """Отсутствующий root_key вызывает ошибку."""
        yaml_content = """
other_key:
  value: 123
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            os.environ["IIKOCLOUD_CONFIG"] = f.name

            try:
                with pytest.raises(ValueError, match="не найден в конфигурации"):
                    get_config(IikoCloudConfig, "iikocloud")
            finally:
                os.environ.pop("IIKOCLOUD_CONFIG", None)
                os.unlink(f.name)


class TestGetIikoCloudConfig:
    """Тесты для get_iikocloud_config."""

    def test_returns_config(self) -> None:
        """Возвращает корректную конфигурацию."""
        yaml_content = """
iikocloud:
  api_login: "my-api-login"
  key_id: "production"
  rate_limits:
    auth:
      max_requests: 5
      time_window_seconds: 2.0
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            os.environ["IIKOCLOUD_CONFIG"] = f.name

            # Очищаем кэш
            parse_config_file.cache_clear()
            get_config.cache_clear()

            try:
                config = get_iikocloud_config()

                assert config.api_login.get_secret_value() == "my-api-login"
                assert config.key_id == "production"
                assert config.rate_limits.auth.max_requests == 5
                assert config.rate_limits.auth.time_window_seconds == 2.0
            finally:
                os.environ.pop("IIKOCLOUD_CONFIG", None)
                os.unlink(f.name)
