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


def test_deliveries_methods_have_limits() -> None:
    """20 методов deliveries есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {"create_delivery_order": 20 / 60.0}
    commands = [
        "add_delivery_order_items",
        "add_delivery_order_payments",
        "cancel_delivery_order",
        "cancel_delivery_confirmation",
        "confirm_delivery",
        "change_delivery_comment",
        "change_delivery_complete_before",
        "change_delivery_driver_info",
        "change_delivery_external_data",
        "change_delivery_operator",
        "change_delivery_payments",
        "change_delivery_point",
        "change_delivery_service_type",
        "close_delivery_order",
        "print_delivery_bill",
        "print_table_order_bill",
        "update_delivery_order_problem",
        "update_delivery_order_status",
        "update_delivery_tracking_link",
    ]
    expected.update({name: 100 / 60.0 for name in commands})

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_delivery_restrictions_methods_have_limits() -> None:
    """2 метода delivery_restrictions есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "get_allowed_delivery_restrictions": 20 / 60.0,
        "get_delivery_restrictions": 1 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_deliveries_retrieve_methods_have_limits() -> None:
    """6 методов deliveries_retrieve есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    names = [
        "get_deliveries_by_delivery_date_and_phone",
        "get_deliveries_by_delivery_date_and_status",
        "get_deliveries_by_id",
        "get_deliveries_by_revision",
        "get_delivery_history_by_delivery_date_and_phone",
        "search_deliveries",
    ]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            10 / 60.0
        )
