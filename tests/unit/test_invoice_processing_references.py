"""Unit tests for Invoice Processing references mixins.

account_transactions / document_transactions / counteragents /
invoice nomenclature (product barcodes).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from iikocloud_client import (
    AccountTransactionsListRequest,
    AccountTransactionsResponse,
    BarcodeItem,
    DocumentTransactionsListRequest,
    GetCounteragentsRequest,
    GetCounteragentsResponse,
    UpdateProductBarcodesRequest,
    UpdateProductBarcodesResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

# Invoice Processing models: organization_id — GUID-СТРОКА, не UUID.
ORG_ID = "00000000-0000-0000-0000-000000000001"
ACCOUNT_ID = "00000000-0000-0000-0000-000000000003"
DOC_ID = "00000000-0000-0000-0000-000000000002"
PRODUCT_ID = "00000000-0000-0000-0000-000000000005"

DATE = "2026-01-01T00:00:00.000+00:00"

ACCOUNT_TRANSACTIONS_METHODS: list[tuple[str, object, str, type]] = [
    (
        "list_finance_account_transactions",
        AccountTransactionsListRequest(
            account_id=ACCOUNT_ID,
            var_from=DATE,
            organization_id=ORG_ID,
            to=DATE,
        ),
        "account_transactions_list_request",
        AccountTransactionsResponse,
    ),
]

DOCUMENT_TRANSACTIONS_METHODS: list[tuple[str, object, str, type]] = [
    (
        "list_finance_document_transactions",
        DocumentTransactionsListRequest(
            document_id=DOC_ID,
            organization_id=ORG_ID,
        ),
        "document_transactions_list_request",
        list,
    ),
]

COUNTERAGENTS_METHODS: list[tuple[str, object, str, type]] = [
    (
        "get_inventory_counteragents",
        GetCounteragentsRequest(organization_id=ORG_ID),
        "get_counteragents_request",
        GetCounteragentsResponse,
    ),
]

INVOICE_NOMENCLATURE_METHODS: list[tuple[str, object, str, type]] = [
    (
        "update_inventory_product_barcodes",
        UpdateProductBarcodesRequest(
            organization_id=ORG_ID,
            product_id=PRODUCT_ID,
            barcodes=[BarcodeItem(barcode="4600000000001")],
        ),
        "update_product_barcodes_request",
        UpdateProductBarcodesResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    ACCOUNT_TRANSACTIONS_METHODS,
)
async def test_account_transactions_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Метод проксирует response с request-моделью."""
    manager, mock_api = await manager_with_stub_api("_account_transactions_api")
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    DOCUMENT_TRANSACTIONS_METHODS,
)
async def test_document_transactions_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Метод проксирует response с request-моделью."""
    manager, mock_api = await manager_with_stub_api("_document_transactions_api")
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    COUNTERAGENTS_METHODS,
)
async def test_counteragents_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Метод проксирует response с request-моделью."""
    manager, mock_api = await manager_with_stub_api("_counteragents_api")
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    INVOICE_NOMENCLATURE_METHODS,
)
async def test_invoice_nomenclature_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Метод проксирует response с request-моделью."""
    manager, mock_api = await manager_with_stub_api("_invoice_nomenclature_api")
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
