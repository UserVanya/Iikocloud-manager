"""Unit tests for Invoice Processing invoice mixins (incoming/outgoing)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from iikocloud_client import (
    AccountingTransactionUserResponse,
    GetByIDRequest,
    GetCostPricesRequest,
    GetCostPricesResponse,
    IncomingInvoice,
    IncomingInvoiceRequest,
    IncomingInvoiceRequestItem,
    IncomingInvoiceSaveResponse,
    ListRequest,
    OutgoingInvoice,
    OutgoingInvoiceRequest,
    OutgoingInvoiceRequestItem,
    OutgoingInvoiceSaveResponse,
    PayOutgoingInvoiceRequest,
    PayRequest,
    PriceItem,
    SetPaymentDateOutgoingRequest,
    SetPaymentDateOutgoingResponse,
    SetPaymentDateRequest,
    SetPaymentDateResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

# Invoice Processing models: organization_id — GUID-СТРОКА, не UUID.
ORG_ID = "00000000-0000-0000-0000-000000000001"
DOC_ID = "00000000-0000-0000-0000-000000000002"
COUNTERAGENT_ID = "00000000-0000-0000-0000-000000000003"
ACCOUNT_ID = "00000000-0000-0000-0000-000000000004"
PRODUCT_ID = "00000000-0000-0000-0000-000000000005"
STORE_ID = "00000000-0000-0000-0000-000000000006"

DATE = "2026-01-01T00:00:00.000+00:00"

GET_BY_ID = GetByIDRequest(document_id=DOC_ID, organization_id=ORG_ID)
LIST = ListRequest(organization_id=ORG_ID, var_from=DATE, to=DATE)

INCOMING_API_SLOT = "_incoming_invoices_api"
OUTGOING_API_SLOT = "_outgoing_invoices_api"

INCOMING_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_incoming_invoice",
        IncomingInvoiceRequest(
            organization_id=ORG_ID,
            counteragent=COUNTERAGENT_ID,
            var_date=DATE,
            items=[
                IncomingInvoiceRequestItem(
                    amount=1.0, num=1, price=100.0,
                    product=PRODUCT_ID, store=STORE_ID,
                )
            ],
        ),
        "incoming_invoice_request",
        IncomingInvoiceSaveResponse,
    ),
    (
        "update_inventory_incoming_invoice",
        IncomingInvoiceRequest(
            organization_id=ORG_ID,
            counteragent=COUNTERAGENT_ID,
            var_date=DATE,
            items=[
                IncomingInvoiceRequestItem(
                    amount=1.0, num=1, price=100.0,
                    product=PRODUCT_ID, store=STORE_ID,
                )
            ],
            document_id=DOC_ID,
        ),
        "incoming_invoice_request",
        IncomingInvoiceSaveResponse,
    ),
    (
        "get_inventory_incoming_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingInvoice,
    ),
    (
        "list_inventory_incoming_invoices",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_incoming_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingInvoiceSaveResponse,
    ),
    (
        "unpost_inventory_incoming_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingInvoiceSaveResponse,
    ),
    (
        "cancel_inventory_incoming_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingInvoiceSaveResponse,
    ),
    (
        "add_inventory_incoming_invoice_payment",
        PayRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            account_from=ACCOUNT_ID,
            var_date=DATE,
            sum=100.0,
        ),
        "pay_request",
        AccountingTransactionUserResponse,
    ),
    (
        "set_inventory_incoming_invoice_payment_date",
        SetPaymentDateRequest(
            document_id=DOC_ID,
            organization_id=ORG_ID,
            payment_date=DATE,
        ),
        "set_payment_date_request",
        SetPaymentDateResponse,
    ),
]

OUTGOING_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_outgoing_invoice",
        OutgoingInvoiceRequest(
            organization_id=ORG_ID,
            counteragent=COUNTERAGENT_ID,
            var_date=DATE,
            items=[
                OutgoingInvoiceRequestItem(
                    amount=1.0, num=1, price=100.0,
                    product=PRODUCT_ID, store=STORE_ID,
                )
            ],
        ),
        "outgoing_invoice_request",
        OutgoingInvoiceSaveResponse,
    ),
    (
        "update_inventory_outgoing_invoice",
        OutgoingInvoiceRequest(
            organization_id=ORG_ID,
            counteragent=COUNTERAGENT_ID,
            var_date=DATE,
            items=[
                OutgoingInvoiceRequestItem(
                    amount=1.0, num=1, price=100.0,
                    product=PRODUCT_ID, store=STORE_ID,
                )
            ],
            document_id=DOC_ID,
        ),
        "outgoing_invoice_request",
        OutgoingInvoiceSaveResponse,
    ),
    (
        "get_inventory_outgoing_invoice",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingInvoice,
    ),
    (
        "list_inventory_outgoing_invoices",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_outgoing_invoice",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingInvoiceSaveResponse,
    ),
    (
        "unpost_inventory_outgoing_invoice",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingInvoiceSaveResponse,
    ),
    (
        "cancel_inventory_outgoing_invoice",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingInvoiceSaveResponse,
    ),
    (
        "add_inventory_outgoing_invoice_payment",
        PayOutgoingInvoiceRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            account_id=ACCOUNT_ID,
            payment_date=DATE,
            amount=100.0,
        ),
        "pay_outgoing_invoice_request",
        AccountingTransactionUserResponse,
    ),
    (
        "set_inventory_outgoing_invoice_payment_date",
        SetPaymentDateOutgoingRequest(
            document_id=DOC_ID,
            organization_id=ORG_ID,
            payment_date=DATE,
        ),
        "set_payment_date_outgoing_request",
        SetPaymentDateOutgoingResponse,
    ),
    (
        "calculate_inventory_cost_prices",
        GetCostPricesRequest(
            organization_id=ORG_ID,
            date_incoming=DATE,
            items=[
                PriceItem(
                    product_id=PRODUCT_ID,
                    store_id=STORE_ID,
                    amount_factor=1.0,
                )
            ],
        ),
        "get_cost_prices_request",
        GetCostPricesResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), INCOMING_METHODS
)
async def test_incoming_invoices_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 9 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(INCOMING_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), OUTGOING_METHODS
)
async def test_outgoing_invoices_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 10 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(OUTGOING_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
