"""Unit tests for Customers domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    AddCustomerToProgramRequest,
    AddCustomerToProgramResponse,
    AddMagnetCardRequest,
    CancelHoldMoneyRequest,
    ChangeUserBalanceRequest,
    CounterMetric,
    CounterPeriod,
    CreateOrUpdateCustomerRequest,
    CreateOrUpdateCustomerResponse,
    DeleteCustomersRequest,
    DeleteCustomersResponse,
    DeleteMagnetCardRequest,
    GetCountersRequest,
    GetCountersResponse,
    GetCustomerInfoByCardNumberRequest,
    GetCustomerInfoByCardTrackRequest,
    GetCustomerInfoByEmailRequest,
    GetCustomerInfoByIdRequest,
    GetCustomerInfoByPhoneRequest,
    GetCustomerInfoResponse,
    HoldMoneyRequest,
    HoldMoneyResponse,
    RestoreCustomersRequest,
    RestoreCustomersResponse,
)

from iikocloud.mixins._base import ApiMethod
from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")


async def test_create_or_update_customer_calls_api_with_request() -> None:
    """create_or_update_customer delegates to SDK with the given request."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    mock_response = MagicMock(spec=CreateOrUpdateCustomerResponse)
    mock_api.create_or_update_customer = AsyncMock(return_value=mock_response)

    request = CreateOrUpdateCustomerRequest(organization_id=ORG_ID)
    result = await manager.create_or_update_customer(request)

    assert result is mock_response
    mock_api.create_or_update_customer.assert_awaited_once_with(
        create_or_update_customer_request=request
    )


async def test_get_customer_info_calls_api_with_request() -> None:
    """get_customer_info delegates to SDK with the given request."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    mock_response = MagicMock(spec=GetCustomerInfoResponse)
    mock_api.get_customer_info = AsyncMock(return_value=mock_response)

    request = GetCustomerInfoByPhoneRequest(
        organization_id=ORG_ID,
        type="phone",
        phone="+79001234567",
    )
    result = await manager.get_customer_info(request)

    assert result is mock_response
    mock_api.get_customer_info.assert_awaited_once_with(
        get_customer_info_request=request
    )


async def test_delete_customers_calls_api_with_request() -> None:
    """delete_customers delegates to SDK with the given request."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    mock_response = MagicMock(spec=DeleteCustomersResponse)
    mock_api.delete_customers = AsyncMock(return_value=mock_response)

    request = DeleteCustomersRequest(
        organization_id=ORG_ID,
        customer_ids=[UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")],
    )
    result = await manager.delete_customers(request)

    assert result is mock_response
    mock_api.delete_customers.assert_awaited_once_with(
        delete_customers_request=request
    )


async def test_restore_customers_calls_api_with_request() -> None:
    """restore_customers delegates to SDK with the given request."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    mock_response = MagicMock(spec=RestoreCustomersResponse)
    mock_api.restore_customers = AsyncMock(return_value=mock_response)

    request = RestoreCustomersRequest(
        organization_id=ORG_ID,
        customer_ids=[UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")],
    )
    result = await manager.restore_customers(request)

    assert result is mock_response
    mock_api.restore_customers.assert_awaited_once_with(
        restore_customers_request=request
    )


async def test_get_customer_by_phone_builds_request_and_delegates() -> None:
    """get_customer_by_phone builds GetCustomerInfoByPhoneRequest and calls core."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    mock_response = MagicMock(spec=GetCustomerInfoResponse)
    mock_api.get_customer_info = AsyncMock(return_value=mock_response)

    result = await manager.get_customer_by_phone(ORG_ID, "+79001234567")

    assert result is mock_response
    mock_api.get_customer_info.assert_awaited_once()
    call_kwargs = mock_api.get_customer_info.await_args.kwargs
    request = call_kwargs["get_customer_info_request"]
    assert isinstance(request, GetCustomerInfoByPhoneRequest)
    assert request.organization_id == ORG_ID
    assert request.type == "phone"
    assert request.phone == "+79001234567"


async def test_get_customer_by_phone_accepts_str_organization_id() -> None:
    """get_customer_by_phone converts string organization_id to UUID."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    mock_api.get_customer_info = AsyncMock(return_value=MagicMock())

    await manager.get_customer_by_phone(str(ORG_ID), "+79001234567")

    call_kwargs = mock_api.get_customer_info.await_args.kwargs
    request = call_kwargs["get_customer_info_request"]
    assert request.organization_id == ORG_ID


async def test_get_customer_by_id_builds_request() -> None:
    """get_customer_by_id builds GetCustomerInfoByIdRequest and calls core."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.get_customer_info = AsyncMock(return_value=MagicMock())
    customer_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    await manager.get_customer_by_id(ORG_ID, customer_id)

    request = mock_api.get_customer_info.await_args.kwargs[
        "get_customer_info_request"
    ]
    assert isinstance(request, GetCustomerInfoByIdRequest)
    assert request.type == "id"
    assert request.id == str(customer_id)
    assert request.organization_id == ORG_ID


async def test_get_customer_by_email_builds_request() -> None:
    """get_customer_by_email builds GetCustomerInfoByEmailRequest and calls core."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.get_customer_info = AsyncMock(return_value=MagicMock())

    await manager.get_customer_by_email(ORG_ID, "user@example.com")

    request = mock_api.get_customer_info.await_args.kwargs[
        "get_customer_info_request"
    ]
    assert isinstance(request, GetCustomerInfoByEmailRequest)
    assert request.type == "email"
    assert request.email == "user@example.com"


async def test_get_customer_by_card_number_builds_request() -> None:
    """get_customer_by_card_number builds cardNumber discriminator request."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.get_customer_info = AsyncMock(return_value=MagicMock())

    await manager.get_customer_by_card_number(ORG_ID, "1234567890")

    request = mock_api.get_customer_info.await_args.kwargs[
        "get_customer_info_request"
    ]
    assert isinstance(request, GetCustomerInfoByCardNumberRequest)
    assert request.type == "cardNumber"
    assert request.card_number == "1234567890"


async def test_get_customer_by_card_track_builds_request() -> None:
    """get_customer_by_card_track builds cardTrack discriminator request."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.get_customer_info = AsyncMock(return_value=MagicMock())

    await manager.get_customer_by_card_track(ORG_ID, ";1234567890?")

    request = mock_api.get_customer_info.await_args.kwargs[
        "get_customer_info_request"
    ]
    assert isinstance(request, GetCustomerInfoByCardTrackRequest)
    assert request.type == "cardTrack"
    assert request.card_track == ";1234567890?"


async def test_add_customer_magnet_card_calls_api() -> None:
    """add_customer_magnet_card delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.add_customer_magnet_card = AsyncMock(return_value={})

    request = AddMagnetCardRequest(
        card_number="123456",
        card_track="track-1",
        customer_id=ORG_ID,
        organization_id=ORG_ID,
    )
    result = await manager.add_customer_magnet_card(request)

    assert result is None
    mock_api.add_customer_magnet_card.assert_awaited_once_with(
        add_magnet_card_request=request
    )


async def test_remove_customer_magnet_card_calls_api() -> None:
    """remove_customer_magnet_card delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.remove_customer_magnet_card = AsyncMock(return_value={})

    request = DeleteMagnetCardRequest(
        card_track="track-1",
        customer_id=ORG_ID,
        organization_id=ORG_ID,
    )
    result = await manager.remove_customer_magnet_card(request)

    assert result is None
    mock_api.remove_customer_magnet_card.assert_awaited_once_with(
        delete_magnet_card_request=request
    )


async def test_add_customer_to_program_returns_response() -> None:
    """add_customer_to_program proxies AddCustomerToProgramResponse."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_response = MagicMock(spec=AddCustomerToProgramResponse)
    mock_api.add_customer_to_program = AsyncMock(return_value=mock_response)

    request = AddCustomerToProgramRequest(
        customer_id=ORG_ID,
        organization_id=ORG_ID,
        program_id=ORG_ID,
    )
    result = await manager.add_customer_to_program(request)

    assert result is mock_response
    mock_api.add_customer_to_program.assert_awaited_once_with(
        add_customer_to_program_request=request
    )


async def test_create_or_update_customer_uses_execute_with_retry() -> None:
    """create_or_update_customer routes through execute_with_retry."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.create_or_update_customer = AsyncMock(return_value=MagicMock())

    async def _passthrough(method, api_call):  # noqa: ANN001
        return await api_call()

    manager.execute_with_retry = AsyncMock(side_effect=_passthrough)

    await manager.create_or_update_customer(
        CreateOrUpdateCustomerRequest(organization_id=ORG_ID)
    )

    manager.execute_with_retry.assert_awaited_once()
    method_arg = manager.execute_with_retry.await_args.args[0]
    assert method_arg is ApiMethod.CREATE_OR_UPDATE_CUSTOMER


async def test_hold_customer_balance_returns_transaction() -> None:
    """hold_customer_balance proxies HoldMoneyResponse."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_response = MagicMock(spec=HoldMoneyResponse)
    mock_api.hold_customer_balance = AsyncMock(return_value=mock_response)

    request = HoldMoneyRequest(
        customer_id=ORG_ID,
        organization_id=ORG_ID,
        wallet_id=ORG_ID,
        sum=100.0,
    )
    result = await manager.hold_customer_balance(request)

    assert result is mock_response
    mock_api.hold_customer_balance.assert_awaited_once_with(
        hold_money_request=request
    )


async def test_cancel_customer_balance_hold_calls_api() -> None:
    """cancel_customer_balance_hold delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.cancel_customer_balance_hold = AsyncMock(return_value={})

    request = CancelHoldMoneyRequest(
        organization_id=ORG_ID,
        transaction_id=ORG_ID,
    )
    result = await manager.cancel_customer_balance_hold(request)

    assert result is None
    mock_api.cancel_customer_balance_hold.assert_awaited_once_with(
        cancel_hold_money_request=request
    )


async def test_top_up_customer_balance_calls_api() -> None:
    """top_up_customer_balance delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.top_up_customer_balance = AsyncMock(return_value={})

    request = ChangeUserBalanceRequest(
        organization_id=ORG_ID,
        customer_id=ORG_ID,
        wallet_id=ORG_ID,
        sum=50.0,
    )
    result = await manager.top_up_customer_balance(request)

    assert result is None
    mock_api.top_up_customer_balance.assert_awaited_once_with(
        change_user_balance_request=request
    )


async def test_withdraw_customer_balance_calls_api() -> None:
    """withdraw_customer_balance delegates to SDK; empty object -> None."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_api.withdraw_customer_balance = AsyncMock(return_value={})

    request = ChangeUserBalanceRequest(
        organization_id=ORG_ID,
        customer_id=ORG_ID,
        wallet_id=ORG_ID,
        sum=50.0,
    )
    result = await manager.withdraw_customer_balance(request)

    assert result is None
    mock_api.withdraw_customer_balance.assert_awaited_once_with(
        change_user_balance_request=request
    )


async def test_get_loyalty_counters_returns_response() -> None:
    """get_loyalty_counters proxies GetCountersResponse."""
    manager, mock_api = await manager_with_stub_api("_customers_api")
    mock_response = MagicMock(spec=GetCountersResponse)
    mock_api.get_loyalty_counters = AsyncMock(return_value=mock_response)

    request = GetCountersRequest(
        organization_id=ORG_ID,
        guest_ids=[ORG_ID],
        metrics=[CounterMetric.NUMBER_0],
        periods=[CounterPeriod.NUMBER_0],
    )
    result = await manager.get_loyalty_counters(request)

    assert result is mock_response
    mock_api.get_loyalty_counters.assert_awaited_once_with(
        get_counters_request=request
    )


@pytest.mark.parametrize(
    "method_name", ["top_up_customer_balance", "withdraw_customer_balance"]
)
async def test_balance_change_requires_customer_and_wallet(method_name: str) -> None:
    """top_up/withdraw без customer_id или wallet_id -> ValueError, SDK не вызывается."""
    manager, mock_api = await manager_with_stub_api("_customers_api")

    for kwargs in (
        {"customer_id": None, "wallet_id": ORG_ID},
        {"customer_id": ORG_ID, "wallet_id": None},
    ):
        request = ChangeUserBalanceRequest(
            organization_id=ORG_ID, sum=10.0, **kwargs
        )
        with pytest.raises(ValueError, match="customer_id"):
            await getattr(manager, method_name)(request)
    mock_api.assert_not_called()
