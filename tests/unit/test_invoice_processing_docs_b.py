"""Unit tests for Invoice Processing docs group B + services mixins.

incoming_returned / internal_transfer / returned / sales documents
+ incoming_service / outgoing_service.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from iikocloud_client import (
    GetByIDRequest,
    IncomingReturnedInvoiceCreateItem,
    IncomingReturnedInvoiceCreateRequest,
    IncomingReturnedInvoiceGetResponse,
    IncomingReturnedInvoiceSaveResponse,
    IncomingReturnedInvoiceUpdateRequest,
    IncomingServiceCreateItem,
    IncomingServiceCreateRequest,
    IncomingServiceGetResponse,
    IncomingServiceSaveResponse,
    IncomingServiceUpdateRequest,
    InternalTransferCreateItem,
    InternalTransferCreateRequest,
    InternalTransferGetResponse,
    InternalTransferSaveResponse,
    InternalTransferUpdateRequest,
    ListRequest,
    OutgoingServiceCreateItem,
    OutgoingServiceCreateRequest,
    OutgoingServiceGetResponse,
    OutgoingServiceSaveResponse,
    OutgoingServiceUpdateRequest,
    ReturnedInvoiceCreateItem,
    ReturnedInvoiceCreateRequest,
    ReturnedInvoiceGetResponse,
    ReturnedInvoiceSaveResponse,
    ReturnedInvoiceUpdateRequest,
    SalesDocumentCreateItem,
    SalesDocumentCreateRequest,
    SalesDocumentGetResponse,
    SalesDocumentSaveResponse,
    SalesDocumentUpdateRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

# Invoice Processing models: organization_id — GUID-СТРОКА, не UUID.
ORG_ID = "00000000-0000-0000-0000-000000000001"
DOC_ID = "00000000-0000-0000-0000-000000000002"
COUNTERAGENT_ID = "00000000-0000-0000-0000-000000000003"
PRODUCT_ID = "00000000-0000-0000-0000-000000000005"
STORE_FROM_ID = "00000000-0000-0000-0000-000000000006"
STORE_TO_ID = "00000000-0000-0000-0000-000000000007"

DATE = "2026-01-01T00:00:00.000+00:00"

GET_BY_ID = GetByIDRequest(document_id=DOC_ID, organization_id=ORG_ID)
LIST = ListRequest(organization_id=ORG_ID, var_from=DATE, to=DATE)

INCOMING_RETURNED_API_SLOT = "_incoming_returned_invoice_api"
INTERNAL_TRANSFER_API_SLOT = "_internal_transfer_api"
RETURNED_API_SLOT = "_returned_invoice_api"
SALES_API_SLOT = "_sales_document_api"
INCOMING_SERVICE_API_SLOT = "_incoming_service_api"
OUTGOING_SERVICE_API_SLOT = "_outgoing_service_api"

INCOMING_RETURNED_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_incoming_returned_invoice",
        IncomingReturnedInvoiceCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            processing_mode="single",
            items=[
                IncomingReturnedInvoiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    store=STORE_FROM_ID,
                )
            ],
        ),
        "incoming_returned_invoice_create_request",
        IncomingReturnedInvoiceSaveResponse,
    ),
    (
        "update_inventory_incoming_returned_invoice",
        IncomingReturnedInvoiceUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            processing_mode="single",
            items=[
                IncomingReturnedInvoiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    store=STORE_FROM_ID,
                )
            ],
        ),
        "incoming_returned_invoice_update_request",
        IncomingReturnedInvoiceSaveResponse,
    ),
    (
        "get_inventory_incoming_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingReturnedInvoiceGetResponse,
    ),
    (
        "list_inventory_incoming_returned_invoices",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_incoming_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingReturnedInvoiceSaveResponse,
    ),
    (
        "unpost_inventory_incoming_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingReturnedInvoiceSaveResponse,
    ),
    (
        "cancel_inventory_incoming_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        IncomingReturnedInvoiceSaveResponse,
    ),
]

INTERNAL_TRANSFER_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_internal_transfer",
        InternalTransferCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                InternalTransferCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "internal_transfer_create_request",
        InternalTransferSaveResponse,
    ),
    (
        "update_inventory_internal_transfer",
        InternalTransferUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                InternalTransferCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "internal_transfer_update_request",
        InternalTransferSaveResponse,
    ),
    (
        "get_inventory_internal_transfer",
        GET_BY_ID,
        "get_by_id_request",
        InternalTransferGetResponse,
    ),
    (
        "list_inventory_internal_transfers",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_internal_transfer",
        GET_BY_ID,
        "get_by_id_request",
        InternalTransferSaveResponse,
    ),
    (
        "unpost_inventory_internal_transfer",
        GET_BY_ID,
        "get_by_id_request",
        InternalTransferSaveResponse,
    ),
    (
        "cancel_inventory_internal_transfer",
        GET_BY_ID,
        "get_by_id_request",
        InternalTransferSaveResponse,
    ),
]

RETURNED_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_returned_invoice",
        ReturnedInvoiceCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            items=[
                ReturnedInvoiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    store=STORE_FROM_ID,
                )
            ],
        ),
        "returned_invoice_create_request",
        ReturnedInvoiceSaveResponse,
    ),
    (
        "update_inventory_returned_invoice",
        ReturnedInvoiceUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            items=[
                ReturnedInvoiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    store=STORE_FROM_ID,
                )
            ],
        ),
        "returned_invoice_update_request",
        ReturnedInvoiceSaveResponse,
    ),
    (
        "get_inventory_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        ReturnedInvoiceGetResponse,
    ),
    (
        "list_inventory_returned_invoices",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        ReturnedInvoiceSaveResponse,
    ),
    (
        "unpost_inventory_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        ReturnedInvoiceSaveResponse,
    ),
    (
        "cancel_inventory_returned_invoice",
        GET_BY_ID,
        "get_by_id_request",
        ReturnedInvoiceSaveResponse,
    ),
]

SALES_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_sales_document",
        SalesDocumentCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            items=[
                SalesDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "sales_document_create_request",
        SalesDocumentSaveResponse,
    ),
    (
        "update_inventory_sales_document",
        SalesDocumentUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            items=[
                SalesDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "sales_document_update_request",
        SalesDocumentSaveResponse,
    ),
    (
        "get_inventory_sales_document",
        GET_BY_ID,
        "get_by_id_request",
        SalesDocumentGetResponse,
    ),
    (
        "list_inventory_sales_documents",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_sales_document",
        GET_BY_ID,
        "get_by_id_request",
        SalesDocumentSaveResponse,
    ),
    (
        "unpost_inventory_sales_document",
        GET_BY_ID,
        "get_by_id_request",
        SalesDocumentSaveResponse,
    ),
    (
        "cancel_inventory_sales_document",
        GET_BY_ID,
        "get_by_id_request",
        SalesDocumentSaveResponse,
    ),
]

INCOMING_SERVICE_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_finance_incoming_service",
        IncomingServiceCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            items=[
                IncomingServiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    revenue_account="90.1",
                    vat_percent=20.0,
                )
            ],
        ),
        "incoming_service_create_request",
        IncomingServiceSaveResponse,
    ),
    (
        "update_finance_incoming_service",
        IncomingServiceUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            items=[
                IncomingServiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    revenue_account="90.1",
                    vat_percent=20.0,
                )
            ],
        ),
        "incoming_service_update_request",
        IncomingServiceSaveResponse,
    ),
    (
        "get_finance_incoming_service",
        GET_BY_ID,
        "get_by_id_request",
        IncomingServiceGetResponse,
    ),
    (
        "list_finance_incoming_services",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_finance_incoming_service",
        GET_BY_ID,
        "get_by_id_request",
        IncomingServiceSaveResponse,
    ),
    (
        "unpost_finance_incoming_service",
        GET_BY_ID,
        "get_by_id_request",
        IncomingServiceSaveResponse,
    ),
    (
        "cancel_finance_incoming_service",
        GET_BY_ID,
        "get_by_id_request",
        IncomingServiceSaveResponse,
    ),
]

OUTGOING_SERVICE_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_finance_outgoing_service",
        OutgoingServiceCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            items=[
                OutgoingServiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    revenue_account="90.1",
                    vat_percent=20.0,
                )
            ],
        ),
        "outgoing_service_create_request",
        OutgoingServiceSaveResponse,
    ),
    (
        "update_finance_outgoing_service",
        OutgoingServiceUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            counteragent=COUNTERAGENT_ID,
            items=[
                OutgoingServiceCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                    revenue_account="90.1",
                    vat_percent=20.0,
                )
            ],
        ),
        "outgoing_service_update_request",
        OutgoingServiceSaveResponse,
    ),
    (
        "get_finance_outgoing_service",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingServiceGetResponse,
    ),
    (
        "list_finance_outgoing_services",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_finance_outgoing_service",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingServiceSaveResponse,
    ),
    (
        "unpost_finance_outgoing_service",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingServiceSaveResponse,
    ),
    (
        "cancel_finance_outgoing_service",
        GET_BY_ID,
        "get_by_id_request",
        OutgoingServiceSaveResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    INCOMING_RETURNED_METHODS,
)
async def test_incoming_returned_invoice_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(INCOMING_RETURNED_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    INTERNAL_TRANSFER_METHODS,
)
async def test_internal_transfer_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(INTERNAL_TRANSFER_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), RETURNED_METHODS
)
async def test_returned_invoice_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(RETURNED_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), SALES_METHODS
)
async def test_sales_document_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(SALES_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    INCOMING_SERVICE_METHODS,
)
async def test_incoming_service_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(INCOMING_SERVICE_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    OUTGOING_SERVICE_METHODS,
)
async def test_outgoing_service_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(OUTGOING_SERVICE_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
