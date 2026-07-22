import pytest
from pydantic import SecretStr

from iikocloud.config_reader import IikoCloudConfig, MethodRateLimitsSettings

pytestmark = pytest.mark.unit


def test_config_requires_v2_fields() -> None:
    cfg = IikoCloudConfig(
        api_key=SecretStr("k"),
        app_id="app",
        client_secret=SecretStr("secret"),
    )
    assert cfg.api_key.get_secret_value() == "k"
    assert cfg.app_id == "app"
    assert "api_login" not in IikoCloudConfig.model_fields
    assert "key_id" not in IikoCloudConfig.model_fields


def test_rate_limits_use_semantic_keys() -> None:
    s = MethodRateLimitsSettings()
    assert hasattr(s, "check_terminal_groups_availability")
    assert hasattr(s, "get_external_menu_by_id")
    assert hasattr(s, "get_cancel_causes")
    assert hasattr(s, "get_delivery_order_types")
    assert hasattr(s, "get_tips_types")
    assert not hasattr(s, "check_terminal_groups_alive")
