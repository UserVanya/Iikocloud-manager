"""Unit tests for Drafts domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CommitDraftRequest,
    CorrelationIdResponse,
    CreateDraftRequest,
    CreateOrSaveDraftResponse,
    DeleteDraftRequest,
    DeliveryOrderCreateProductItem,
    DeliveryOrderDraft,
    FilterDraftsRequest,
    FilterDraftsResponse,
    GetDraftRequest,
    GetDraftResponse,
    LockOrUnlockDraftRequest,
    OrderResponse,
    SaveDraftRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_drafts_api"

DRAFT = DeliveryOrderDraft(
    menu_id="m",
    phone="+79990001122",
    items=[
        DeliveryOrderCreateProductItem(
            type="Product", product_id=ORG_ID, amount=1.0, price=1.0
        )
    ],
)

CORRELATION_METHODS = [
    (
        "delete_delivery_draft",
        DeleteDraftRequest(organization_id=ORG_ID, order_id=ORG_ID),
        "delete_draft_request",
    ),
    (
        "lock_delivery_draft",
        LockOrUnlockDraftRequest(
            organization_id=ORG_ID, order_id=ORG_ID, employee_id=ORG_ID
        ),
        "lock_or_unlock_draft_request",
    ),
    (
        "unlock_delivery_draft",
        LockOrUnlockDraftRequest(
            organization_id=ORG_ID, order_id=ORG_ID, employee_id=ORG_ID
        ),
        "lock_or_unlock_draft_request",
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg"), CORRELATION_METHODS
)
async def test_correlation_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str
) -> None:
    """delete/lock/unlock -> CorrelationIdResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CorrelationIdResponse)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


async def test_create_delivery_draft_returns_order_id() -> None:
    """create_delivery_draft проксирует CreateOrSaveDraftResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CreateOrSaveDraftResponse)
    mock_api.create_delivery_draft = AsyncMock(return_value=mock_response)

    request = CreateDraftRequest(organization_id=ORG_ID, order=DRAFT)
    result = await manager.create_delivery_draft(request)

    assert result is mock_response
    mock_api.create_delivery_draft.assert_awaited_once_with(
        create_draft_request=request
    )


async def test_save_delivery_draft_returns_order_id() -> None:
    """save_delivery_draft проксирует CreateOrSaveDraftResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=CreateOrSaveDraftResponse)
    mock_api.save_delivery_draft = AsyncMock(return_value=mock_response)

    request = SaveDraftRequest(
        organization_id=ORG_ID, employee_id=ORG_ID, order=DRAFT
    )
    result = await manager.save_delivery_draft(request)

    assert result is mock_response
    mock_api.save_delivery_draft.assert_awaited_once_with(
        save_draft_request=request
    )


async def test_commit_delivery_draft_returns_order_response() -> None:
    """commit_delivery_draft проксирует OrderResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=OrderResponse)
    mock_api.commit_delivery_draft = AsyncMock(return_value=mock_response)

    request = CommitDraftRequest(organization_id=ORG_ID, order_id=ORG_ID)
    result = await manager.commit_delivery_draft(request)

    assert result is mock_response
    mock_api.commit_delivery_draft.assert_awaited_once_with(
        commit_draft_request=request
    )


async def test_get_delivery_draft_by_id_returns_draft() -> None:
    """get_delivery_draft_by_id проксирует GetDraftResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetDraftResponse)
    mock_api.get_delivery_draft_by_id = AsyncMock(return_value=mock_response)

    request = GetDraftRequest(organization_id=ORG_ID, order_id=ORG_ID)
    result = await manager.get_delivery_draft_by_id(request)

    assert result is mock_response
    mock_api.get_delivery_draft_by_id.assert_awaited_once_with(
        get_draft_request=request
    )


async def test_get_delivery_drafts_by_filter_returns_list() -> None:
    """get_delivery_drafts_by_filter проксирует FilterDraftsResponse."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=FilterDraftsResponse)
    mock_api.get_delivery_drafts_by_filter = AsyncMock(
        return_value=mock_response
    )

    request = FilterDraftsRequest(organization_ids=[ORG_ID])
    result = await manager.get_delivery_drafts_by_filter(request)

    assert result is mock_response
    mock_api.get_delivery_drafts_by_filter.assert_awaited_once_with(
        filter_drafts_request=request
    )
