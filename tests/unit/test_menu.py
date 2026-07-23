"""Unit tests for Menu domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    AddProductsToStopListItem,
    AddProductsToStopListRequest,
    CalculateComboPriceRequest,
    CalculateComboPriceResponse,
    CheckStopListRequest,
    CheckStopListResponse,
    ClearStopListRequest,
    CorrelationIdResponse,
    DeliveryOrderCreateProductItem,
    ExternalMenuResponse,
    GetCombosInfoRequest,
    GetCombosInfoResponse,
    MenuRequest,
    MenusDataResponse,
    NomenclatureRequest,
    NomenclatureResponse,
    RemoveProductsFromStopListItem,
    RemoveProductsFromStopListRequest,
    StopListsRequest,
    StopListsResponse,
)

from iikocloud.mixins._base import ApiMethod
from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
MENU_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


async def test_get_external_menus_calls_api() -> None:
    """get_external_menus delegates to SDK without a request body."""
    manager, mock_api = await manager_with_stub_api("_menu_api")

    mock_response = MagicMock(spec=MenusDataResponse)
    mock_api.get_external_menus = AsyncMock(return_value=mock_response)

    result = await manager.get_external_menus()

    assert result is mock_response
    mock_api.get_external_menus.assert_awaited_once_with()


async def test_get_external_menu_by_id_calls_api_with_request() -> None:
    """get_external_menu_by_id delegates to SDK with MenuRequest."""
    manager, mock_api = await manager_with_stub_api("_menu_api")

    mock_response = MagicMock(spec=ExternalMenuResponse)
    mock_api.get_external_menu_by_id = AsyncMock(return_value=mock_response)

    request = MenuRequest(
        external_menu_id=MENU_ID,
        organization_ids=[ORG_ID],
    )
    result = await manager.get_external_menu_by_id(request)

    assert result is mock_response
    mock_api.get_external_menu_by_id.assert_awaited_once_with(
        menu_request=request
    )


async def test_get_stop_lists_calls_api_with_request() -> None:
    """get_stop_lists delegates to SDK with StopListsRequest."""
    manager, mock_api = await manager_with_stub_api("_menu_api")

    mock_response = MagicMock(spec=StopListsResponse)
    mock_api.get_stop_lists = AsyncMock(return_value=mock_response)

    request = StopListsRequest(organization_ids=[ORG_ID])
    result = await manager.get_stop_lists(request)

    assert result is mock_response
    mock_api.get_stop_lists.assert_awaited_once_with(
        stop_lists_request=request
    )


async def test_get_stop_lists_by_organization_builds_request() -> None:
    """get_stop_lists_by_organization builds StopListsRequest."""
    manager, mock_api = await manager_with_stub_api("_menu_api")

    mock_response = MagicMock(spec=StopListsResponse)
    mock_api.get_stop_lists = AsyncMock(return_value=mock_response)

    result = await manager.get_stop_lists_by_organization(ORG_ID)

    assert result is mock_response
    mock_api.get_stop_lists.assert_awaited_once()
    call_kwargs = mock_api.get_stop_lists.await_args.kwargs
    request = call_kwargs["stop_lists_request"]
    assert isinstance(request, StopListsRequest)
    assert request.organization_ids == [ORG_ID]


async def test_get_stop_lists_by_organization_accepts_str_id() -> None:
    """get_stop_lists_by_organization converts string organization_id."""
    manager, mock_api = await manager_with_stub_api("_menu_api")

    mock_api.get_stop_lists = AsyncMock(return_value=MagicMock())

    await manager.get_stop_lists_by_organization(str(ORG_ID))

    call_kwargs = mock_api.get_stop_lists.await_args.kwargs
    request = call_kwargs["stop_lists_request"]
    assert request.organization_ids == [ORG_ID]


async def test_get_external_menus_uses_execute_with_retry() -> None:
    """get_external_menus routes through execute_with_retry."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_api.get_external_menus = AsyncMock(return_value=MagicMock())

    async def _passthrough(method, api_call):  # noqa: ANN001
        return await api_call()

    manager.execute_with_retry = AsyncMock(side_effect=_passthrough)

    await manager.get_external_menus()

    manager.execute_with_retry.assert_awaited_once()
    method_arg = manager.execute_with_retry.await_args.args[0]
    assert method_arg is ApiMethod.GET_EXTERNAL_MENUS


async def test_add_products_to_stop_list_returns_correlation() -> None:
    """add_products_to_stop_list proxies CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.add_products_to_stop_list = AsyncMock(return_value=mock_response)

    request = AddProductsToStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
        items=[AddProductsToStopListItem(product_id=ORG_ID, balance=0.0)],
    )
    result = await manager.add_products_to_stop_list(request)

    assert result is mock_response
    mock_api.add_products_to_stop_list.assert_awaited_once_with(
        add_products_to_stop_list_request=request
    )


async def test_remove_products_from_stop_list_returns_correlation() -> None:
    """remove_products_from_stop_list proxies CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.remove_products_from_stop_list = AsyncMock(return_value=mock_response)

    request = RemoveProductsFromStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
        items=[RemoveProductsFromStopListItem(product_id=ORG_ID)],
    )
    result = await manager.remove_products_from_stop_list(request)

    assert result is mock_response
    mock_api.remove_products_from_stop_list.assert_awaited_once_with(
        remove_products_from_stop_list_request=request
    )


async def test_clear_stop_list_returns_correlation() -> None:
    """clear_stop_list proxies CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CorrelationIdResponse)
    mock_api.clear_stop_list = AsyncMock(return_value=mock_response)

    request = ClearStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
    )
    result = await manager.clear_stop_list(request)

    assert result is mock_response
    mock_api.clear_stop_list.assert_awaited_once_with(
        clear_stop_list_request=request
    )


async def test_check_products_in_stop_list_returns_response() -> None:
    """check_products_in_stop_list proxies CheckStopListResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CheckStopListResponse)
    mock_api.check_products_in_stop_list = AsyncMock(return_value=mock_response)

    request = CheckStopListRequest(
        organization_id=ORG_ID,
        terminal_group_id=ORG_ID,
        items=[
            DeliveryOrderCreateProductItem(
                type="Product",
                product_id=ORG_ID,
                amount=1.0,
                price=1.0,
            )
        ],
    )
    result = await manager.check_products_in_stop_list(request)

    assert result is mock_response
    mock_api.check_products_in_stop_list.assert_awaited_once_with(
        check_stop_list_request=request
    )


async def test_get_nomenclature_returns_response() -> None:
    """get_nomenclature proxies NomenclatureResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=NomenclatureResponse)
    mock_api.get_nomenclature = AsyncMock(return_value=mock_response)

    request = NomenclatureRequest(organization_id=ORG_ID, start_revision=0)
    result = await manager.get_nomenclature(request)

    assert result is mock_response
    mock_api.get_nomenclature.assert_awaited_once_with(
        nomenclature_request=request
    )


async def test_get_combos_info_returns_response() -> None:
    """get_combos_info proxies GetCombosInfoResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=GetCombosInfoResponse)
    mock_api.get_combos_info = AsyncMock(return_value=mock_response)

    request = GetCombosInfoRequest(organization_id=ORG_ID)
    result = await manager.get_combos_info(request)

    assert result is mock_response
    mock_api.get_combos_info.assert_awaited_once_with(
        get_combos_info_request=request
    )


async def test_calculate_combo_price_returns_response() -> None:
    """calculate_combo_price proxies CalculateComboPriceResponse."""
    manager, mock_api = await manager_with_stub_api("_menu_api")
    mock_response = MagicMock(spec=CalculateComboPriceResponse)
    mock_api.calculate_combo_price = AsyncMock(return_value=mock_response)

    request = CalculateComboPriceRequest(
        organization_id=ORG_ID,
        items=[
            DeliveryOrderCreateProductItem(
                type="Product",
                product_id=ORG_ID,
                amount=1.0,
                price=1.0,
            )
        ],
    )
    result = await manager.calculate_combo_price(request)

    assert result is mock_response
    mock_api.calculate_combo_price.assert_awaited_once_with(
        calculate_combo_price_request=request
    )
