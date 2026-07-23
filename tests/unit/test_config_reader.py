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


def test_new_extension_methods_have_limits() -> None:
    """15 новых методов customers+/menu+ есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "add_customer_magnet_card": 100 / 60.0,
        "remove_customer_magnet_card": 100 / 60.0,
        "add_customer_to_program": 100 / 60.0,
        "hold_customer_balance": 100 / 60.0,
        "cancel_customer_balance_hold": 100 / 60.0,
        "top_up_customer_balance": 100 / 60.0,
        "withdraw_customer_balance": 100 / 60.0,
        "get_loyalty_counters": 10 / 60.0,
        "add_products_to_stop_list": 1 / 60.0,
        "remove_products_from_stop_list": 1 / 60.0,
        "clear_stop_list": 1 / 60.0,
        "check_products_in_stop_list": 10 / 60.0,
        "get_nomenclature": 1 / 60.0,
        "get_combos_info": 10 / 60.0,
        "calculate_combo_price": 10 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        method = ApiMethod(name)
        config = limits.for_method(method)
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)
