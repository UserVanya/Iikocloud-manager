"""Unit tests for CustomerCategories domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    ChangeCategoryForCustomerRequest,
    GetCategoriesRequest,
    GetCategoriesResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_customer_categories_api"


async def test_get_customer_categories_delegates() -> None:
    """get_customer_categories проксирует response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=GetCategoriesResponse)
    mock_api.get_customer_categories = AsyncMock(return_value=mock_response)

    request = GetCategoriesRequest(organization_id=ORG_ID)
    result = await manager.get_customer_categories(request)

    assert result is mock_response
    mock_api.get_customer_categories.assert_awaited_once_with(
        get_categories_request=request
    )


async def test_add_customer_category_returns_none() -> None:
    """add_customer_category: object-ответ -> None."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.add_customer_category = AsyncMock(return_value={})

    request = ChangeCategoryForCustomerRequest(
        category_id=ORG_ID, customer_id=ORG_ID, organization_id=ORG_ID
    )
    result = await manager.add_customer_category(request)

    assert result is None
    mock_api.add_customer_category.assert_awaited_once_with(
        change_category_for_customer_request=request
    )


async def test_remove_customer_category_returns_none() -> None:
    """remove_customer_category: object-ответ -> None."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.remove_customer_category = AsyncMock(return_value={})

    request = ChangeCategoryForCustomerRequest(
        category_id=ORG_ID, customer_id=ORG_ID, organization_id=ORG_ID
    )
    result = await manager.remove_customer_category(request)

    assert result is None
    mock_api.remove_customer_category.assert_awaited_once_with(
        change_category_for_customer_request=request
    )
