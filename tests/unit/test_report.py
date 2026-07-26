"""Unit tests for Report domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    GetTransactionsReportByPeriodRequest,
    GetTransactionsReportByPeriodResponse,
    GetTransactionsReportByRevisionRequest,
    GetTransactionsReportByRevisionResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_report_api"

METHODS: list[tuple[str, object, str, type]] = [
    (
        "get_customer_transactions_by_date",
        GetTransactionsReportByPeriodRequest(
            customer_id=ORG_ID,
            organization_id=ORG_ID,
            date_from="2026-07-01 00:00:00.000",
            date_to="2026-07-25 00:00:00.000",
            page_number=0,
            page_size=10,
        ),
        "get_transactions_report_by_period_request",
        GetTransactionsReportByPeriodResponse,
    ),
    (
        "get_customer_transactions_by_revision",
        GetTransactionsReportByRevisionRequest(
            customer_id=ORG_ID, organization_id=ORG_ID, page_size=10
        ),
        "get_transactions_report_by_revision_request",
        GetTransactionsReportByRevisionResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_report_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Оба метода проксируют response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
