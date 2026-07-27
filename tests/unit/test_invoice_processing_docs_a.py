"""Unit tests for Invoice Processing docs group A mixins.

disassemble / production / transformation / writeoff documents.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from iikocloud_client import (
    DisassembleDocumentCreateItem,
    DisassembleDocumentCreateRequest,
    DisassembleDocumentGetResponse,
    DisassembleDocumentSaveResponse,
    DisassembleDocumentUpdateRequest,
    GetByIDRequest,
    ListRequest,
    ProductionDocumentCreateItem,
    ProductionDocumentCreateRequest,
    ProductionDocumentGetResponse,
    ProductionDocumentSaveResponse,
    ProductionDocumentUpdateRequest,
    TransformationDocumentCreateItem,
    TransformationDocumentCreateRequest,
    TransformationDocumentGetResponse,
    TransformationDocumentSaveResponse,
    TransformationDocumentUpdateRequest,
    WriteoffDocumentCreateItem,
    WriteoffDocumentCreateRequest,
    WriteoffDocumentGetResponse,
    WriteoffDocumentSaveResponse,
    WriteoffDocumentUpdateRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

# Invoice Processing models: organization_id — GUID-СТРОКА, не UUID.
ORG_ID = "00000000-0000-0000-0000-000000000001"
DOC_ID = "00000000-0000-0000-0000-000000000002"
PRODUCT_ID = "00000000-0000-0000-0000-000000000005"
STORE_FROM_ID = "00000000-0000-0000-0000-000000000006"
STORE_TO_ID = "00000000-0000-0000-0000-000000000007"

DATE = "2026-01-01T00:00:00.000+00:00"

GET_BY_ID = GetByIDRequest(document_id=DOC_ID, organization_id=ORG_ID)
LIST = ListRequest(organization_id=ORG_ID, var_from=DATE, to=DATE)

DISASSEMBLE_API_SLOT = "_disassemble_document_api"
PRODUCTION_API_SLOT = "_production_document_api"
TRANSFORMATION_API_SLOT = "_transformation_document_api"
WRITEOFF_API_SLOT = "_writeoff_document_api"

DISASSEMBLE_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_disassemble_document",
        DisassembleDocumentCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            product=PRODUCT_ID,
            amount=1.0,
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                DisassembleDocumentCreateItem(
                    amount=1.0,
                    main_product_amount_percent=100.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "disassemble_document_create_request",
        DisassembleDocumentSaveResponse,
    ),
    (
        "update_inventory_disassemble_document",
        DisassembleDocumentUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            product=PRODUCT_ID,
            amount=1.0,
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                DisassembleDocumentCreateItem(
                    amount=1.0,
                    main_product_amount_percent=100.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "disassemble_document_update_request",
        DisassembleDocumentSaveResponse,
    ),
    (
        "get_inventory_disassemble_document",
        GET_BY_ID,
        "get_by_id_request",
        DisassembleDocumentGetResponse,
    ),
    (
        "list_inventory_disassemble_documents",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_disassemble_document",
        GET_BY_ID,
        "get_by_id_request",
        DisassembleDocumentSaveResponse,
    ),
    (
        "unpost_inventory_disassemble_document",
        GET_BY_ID,
        "get_by_id_request",
        DisassembleDocumentSaveResponse,
    ),
    (
        "cancel_inventory_disassemble_document",
        GET_BY_ID,
        "get_by_id_request",
        DisassembleDocumentSaveResponse,
    ),
]

PRODUCTION_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_production_document",
        ProductionDocumentCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                ProductionDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "production_document_create_request",
        ProductionDocumentSaveResponse,
    ),
    (
        "update_inventory_production_document",
        ProductionDocumentUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                ProductionDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "production_document_update_request",
        ProductionDocumentSaveResponse,
    ),
    (
        "get_inventory_production_document",
        GET_BY_ID,
        "get_by_id_request",
        ProductionDocumentGetResponse,
    ),
    (
        "list_inventory_production_documents",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_production_document",
        GET_BY_ID,
        "get_by_id_request",
        ProductionDocumentSaveResponse,
    ),
    (
        "unpost_inventory_production_document",
        GET_BY_ID,
        "get_by_id_request",
        ProductionDocumentSaveResponse,
    ),
    (
        "cancel_inventory_production_document",
        GET_BY_ID,
        "get_by_id_request",
        ProductionDocumentSaveResponse,
    ),
]

TRANSFORMATION_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_transformation_document",
        TransformationDocumentCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            product=PRODUCT_ID,
            amount=1.0,
            amount_unit="kg",
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                TransformationDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "transformation_document_create_request",
        TransformationDocumentSaveResponse,
    ),
    (
        "update_inventory_transformation_document",
        TransformationDocumentUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            product=PRODUCT_ID,
            amount=1.0,
            amount_unit="kg",
            store_from=STORE_FROM_ID,
            store_to=STORE_TO_ID,
            items=[
                TransformationDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "transformation_document_update_request",
        TransformationDocumentSaveResponse,
    ),
    (
        "get_inventory_transformation_document",
        GET_BY_ID,
        "get_by_id_request",
        TransformationDocumentGetResponse,
    ),
    (
        "list_inventory_transformation_documents",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_transformation_document",
        GET_BY_ID,
        "get_by_id_request",
        TransformationDocumentSaveResponse,
    ),
    (
        "unpost_inventory_transformation_document",
        GET_BY_ID,
        "get_by_id_request",
        TransformationDocumentSaveResponse,
    ),
    (
        "cancel_inventory_transformation_document",
        GET_BY_ID,
        "get_by_id_request",
        TransformationDocumentSaveResponse,
    ),
]

WRITEOFF_METHODS: list[tuple[str, object, str, type]] = [
    (
        "create_inventory_writeoff_document",
        WriteoffDocumentCreateRequest(
            organization_id=ORG_ID,
            var_date=DATE,
            expense_account="1.1",
            store_from=STORE_FROM_ID,
            items=[
                WriteoffDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "writeoff_document_create_request",
        WriteoffDocumentSaveResponse,
    ),
    (
        "update_inventory_writeoff_document",
        WriteoffDocumentUpdateRequest(
            organization_id=ORG_ID,
            document_id=DOC_ID,
            number="100",
            var_date=DATE,
            expense_account="1.1",
            store_from=STORE_FROM_ID,
            items=[
                WriteoffDocumentCreateItem(
                    amount=1.0,
                    num=1,
                    product=PRODUCT_ID,
                )
            ],
        ),
        "writeoff_document_update_request",
        WriteoffDocumentSaveResponse,
    ),
    (
        "get_inventory_writeoff_document",
        GET_BY_ID,
        "get_by_id_request",
        WriteoffDocumentGetResponse,
    ),
    (
        "list_inventory_writeoff_documents",
        LIST,
        "list_request",
        list,
    ),
    (
        "post_inventory_writeoff_document",
        GET_BY_ID,
        "get_by_id_request",
        WriteoffDocumentSaveResponse,
    ),
    (
        "unpost_inventory_writeoff_document",
        GET_BY_ID,
        "get_by_id_request",
        WriteoffDocumentSaveResponse,
    ),
    (
        "cancel_inventory_writeoff_document",
        GET_BY_ID,
        "get_by_id_request",
        WriteoffDocumentSaveResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), DISASSEMBLE_METHODS
)
async def test_disassemble_document_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(DISASSEMBLE_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), PRODUCTION_METHODS
)
async def test_production_document_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(PRODUCTION_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"),
    TRANSFORMATION_METHODS,
)
async def test_transformation_document_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(TRANSFORMATION_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), WRITEOFF_METHODS
)
async def test_writeoff_document_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 7 методов проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(WRITEOFF_API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
