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


def test_drafts_methods_have_limits() -> None:
    """8 методов drafts есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    write_names = [
        "create_delivery_draft",
        "save_delivery_draft",
        "delete_delivery_draft",
        "lock_delivery_draft",
        "unlock_delivery_draft",
    ]
    expected = {name: 100 / 60.0 for name in write_names}
    expected["commit_delivery_draft"] = 20 / 60.0
    expected["get_delivery_draft_by_id"] = 20 / 60.0
    expected["get_delivery_drafts_by_filter"] = 20 / 60.0

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


def test_customer_categories_methods_have_limits() -> None:
    """3 метода customer_categories есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "get_customer_categories": 1 / 60.0,
        "add_customer_category": 100 / 60.0,
        "remove_customer_category": 100 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_addresses_methods_have_limits() -> None:
    """4 метода addresses есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    names = ["get_cities", "get_regions", "get_streets_by_city", "get_streets_by_id"]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            1 / 60.0
        )


def test_discounts_methods_have_limits() -> None:
    """6 методов discounts есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "calculate_loyalty_checkin": 1000 / 60.0,
        "get_coupon_info": 10 / 60.0,
        "get_coupon_series": 1 / 60.0,
        "get_loyalty_manual_conditions": 1 / 60.0,
        "get_loyalty_programs": 1 / 60.0,
        "get_non_activated_coupons_by_series": 10 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_report_methods_have_limits() -> None:
    """2 метода report есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    names = [
        "get_customer_transactions_by_date",
        "get_customer_transactions_by_revision",
    ]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            10 / 60.0
        )


def test_marketing_sources_method_has_limits() -> None:
    """get_marketing_sources есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    config = limits.for_method(ApiMethod("get_marketing_sources"))
    assert config.max_requests / config.time_window_seconds == pytest.approx(
        1 / 60.0
    )


def test_messages_methods_have_limits() -> None:
    """4 метода messages есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "check_sms_sending_possibility": 10 / 60.0,
        "check_sms_status": 10 / 60.0,
        "send_loyalty_sms": 20 / 60.0,
        "send_loyalty_email": 20 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_send_notification_has_limits() -> None:
    """send_notification есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    config = limits.for_method(ApiMethod("send_notification"))
    assert config.max_requests / config.time_window_seconds == pytest.approx(
        100 / 60.0
    )


def test_get_command_status_has_limits() -> None:
    """get_command_status есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    config = limits.for_method(ApiMethod("get_command_status"))
    assert config.max_requests / config.time_window_seconds == pytest.approx(
        60 / 60.0
    )


def test_webhooks_methods_have_limits() -> None:
    """2 метода webhooks есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    names = ["get_webhook_settings", "update_webhook_settings"]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            1 / 60.0
        )


def test_employees_methods_have_limits() -> None:
    """10 методов employees есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    expected = {
        "get_couriers": 1 / 60.0,
        "get_couriers_by_role": 1 / 60.0,
        "get_employee_info": 1 / 60.0,
        "get_active_courier_locations": 10 / 60.0,
        "get_active_courier_locations_by_terminal": 10 / 60.0,
        "get_courier_location_history": 10 / 60.0,
        "get_personal_session_info": 10 / 60.0,
        "get_terminal_groups_of_employee": 10 / 60.0,
        "open_personal_session": 100 / 60.0,
        "close_personal_session": 100 / 60.0,
    }
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_banquets_methods_have_limits() -> None:
    """12 методов banquets есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    read_names = [
        "get_reserve_available_organizations",
        "get_reserve_terminal_groups",
        "get_reserve_restaurant_sections",
        "get_reserve_statuses_by_id",
        "get_restaurant_sections_workload",
    ]
    mutation_names = [
        "add_banquet_order_items",
        "add_banquet_order_payments",
        "cancel_reserve",
        "change_banquet_order_items",
        "change_reserve_estimated_start_time",
        "change_reserve_tables",
    ]
    expected = {name: 20 / 60.0 for name in read_names}
    expected["create_reserve"] = 20 / 60.0
    expected.update({name: 100 / 60.0 for name in mutation_names})

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_orders_methods_have_limits() -> None:
    """12 методов orders есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    read_names = ["get_table_orders_by_id", "get_table_orders_by_table"]
    mutation_names = [
        "add_customer_to_table_order",
        "add_items_to_table_order",
        "add_table_order_payments",
        "change_table_order_payments",
        "change_table_order_external_data",
        "close_table_order",
        "cancel_table_order",
        "initialize_table_orders_by_pos_orders",
        "initialize_table_orders_by_tables",
    ]
    expected = {"create_table_order": 20 / 60.0}
    expected.update({name: 20 / 60.0 for name in read_names})
    expected.update({name: 100 / 60.0 for name in mutation_names})

    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name, rps in expected.items():
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(rps)


def test_invoice_processing_methods_have_limits() -> None:
    """93 метода invoice processing есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    read_names = [
        # get/list документных классов + references — 10/60s
        "get_inventory_disassemble_document",
        "list_inventory_disassemble_documents",
        "get_inventory_incoming_invoice",
        "list_inventory_incoming_invoices",
        "get_inventory_incoming_returned_invoice",
        "list_inventory_incoming_returned_invoices",
        "get_inventory_internal_transfer",
        "list_inventory_internal_transfers",
        "get_inventory_outgoing_invoice",
        "list_inventory_outgoing_invoices",
        "get_inventory_production_document",
        "list_inventory_production_documents",
        "get_inventory_returned_invoice",
        "list_inventory_returned_invoices",
        "get_inventory_sales_document",
        "list_inventory_sales_documents",
        "get_inventory_transformation_document",
        "list_inventory_transformation_documents",
        "get_inventory_writeoff_document",
        "list_inventory_writeoff_documents",
        "get_finance_incoming_service",
        "list_finance_incoming_services",
        "get_finance_outgoing_service",
        "list_finance_outgoing_services",
        "list_finance_account_transactions",
        "list_finance_document_transactions",
        "get_inventory_counteragents",
    ]
    mutation_names = [
        # create/update/post/unpost/cancel/add_payment/set_payment_date/
        # calculate_cost_prices/update_barcodes — 100/60s
        "cancel_inventory_disassemble_document",
        "create_inventory_disassemble_document",
        "post_inventory_disassemble_document",
        "unpost_inventory_disassemble_document",
        "update_inventory_disassemble_document",
        "add_inventory_incoming_invoice_payment",
        "cancel_inventory_incoming_invoice",
        "create_inventory_incoming_invoice",
        "post_inventory_incoming_invoice",
        "set_inventory_incoming_invoice_payment_date",
        "unpost_inventory_incoming_invoice",
        "update_inventory_incoming_invoice",
        "cancel_inventory_incoming_returned_invoice",
        "create_inventory_incoming_returned_invoice",
        "post_inventory_incoming_returned_invoice",
        "unpost_inventory_incoming_returned_invoice",
        "update_inventory_incoming_returned_invoice",
        "cancel_inventory_internal_transfer",
        "create_inventory_internal_transfer",
        "post_inventory_internal_transfer",
        "unpost_inventory_internal_transfer",
        "update_inventory_internal_transfer",
        "add_inventory_outgoing_invoice_payment",
        "calculate_inventory_cost_prices",
        "cancel_inventory_outgoing_invoice",
        "create_inventory_outgoing_invoice",
        "post_inventory_outgoing_invoice",
        "set_inventory_outgoing_invoice_payment_date",
        "unpost_inventory_outgoing_invoice",
        "update_inventory_outgoing_invoice",
        "cancel_inventory_production_document",
        "create_inventory_production_document",
        "post_inventory_production_document",
        "unpost_inventory_production_document",
        "update_inventory_production_document",
        "cancel_inventory_returned_invoice",
        "create_inventory_returned_invoice",
        "post_inventory_returned_invoice",
        "unpost_inventory_returned_invoice",
        "update_inventory_returned_invoice",
        "cancel_inventory_sales_document",
        "create_inventory_sales_document",
        "post_inventory_sales_document",
        "unpost_inventory_sales_document",
        "update_inventory_sales_document",
        "cancel_inventory_transformation_document",
        "create_inventory_transformation_document",
        "post_inventory_transformation_document",
        "unpost_inventory_transformation_document",
        "update_inventory_transformation_document",
        "cancel_inventory_writeoff_document",
        "create_inventory_writeoff_document",
        "post_inventory_writeoff_document",
        "unpost_inventory_writeoff_document",
        "update_inventory_writeoff_document",
        "cancel_finance_incoming_service",
        "create_finance_incoming_service",
        "post_finance_incoming_service",
        "unpost_finance_incoming_service",
        "update_finance_incoming_service",
        "cancel_finance_outgoing_service",
        "create_finance_outgoing_service",
        "post_finance_outgoing_service",
        "unpost_finance_outgoing_service",
        "update_finance_outgoing_service",
        "update_inventory_product_barcodes",
    ]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in read_names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            10 / 60.0
        )
    for name in mutation_names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(
            100 / 60.0
        )
    # страховка от пропуска: ровно 93 метода
    assert len(read_names) + len(mutation_names) == 93


@pytest.mark.unit
def test_menu_limits_match_response_weight():
    """get_external_menus отдаёт лёгкий список, get_external_menu_by_id — меню целиком.

    Лимиты 1/1800s и 5/60s разрешали тяжёлый метод в 150 раз чаще лёгкого."""
    settings = MethodRateLimitsSettings()
    assert settings.get_external_menus.max_requests == 10
    assert settings.get_external_menus.time_window_seconds == 60.0
    assert settings.get_external_menu_by_id.max_requests == 1
    assert settings.get_external_menu_by_id.time_window_seconds == 120.0


@pytest.mark.unit
def test_no_method_window_exceeds_two_minutes():
    settings = MethodRateLimitsSettings()
    too_slow = [
        name for name in type(settings).model_fields
        if getattr(settings, name).time_window_seconds > 120.0
    ]
    assert too_slow == []
