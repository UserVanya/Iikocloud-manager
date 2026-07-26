"""Structure-only read-тесты Report (write-секция через test_server)."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

import pytest
from iikocloud_client import (
    GetTransactionsReportByPeriodRequest,
    GetTransactionsReportByRevisionRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.000"
_FAKE_CUSTOMER = UUID("00000000-0000-0000-0000-000000000001")


class TestCustomerTransactions:
    async def test_transactions_by_date_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """По несуществующему клиенту — валидная структура (список может быть пуст)."""
        date_to = datetime.now()
        date_from = date_to - timedelta(days=30)
        response = await manager.get_customer_transactions_by_date(
            GetTransactionsReportByPeriodRequest(
                customer_id=_FAKE_CUSTOMER,
                organization_id=organization_id,
                date_from=date_from.strftime(_DATE_FORMAT),
                date_to=date_to.strftime(_DATE_FORMAT),
                page_number=0,
                page_size=10,
            )
        )
        assert response is not None
        assert response.transactions is not None

    async def test_transactions_by_revision_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.get_customer_transactions_by_revision(
            GetTransactionsReportByRevisionRequest(
                customer_id=_FAKE_CUSTOMER,
                organization_id=organization_id,
                page_size=10,
            )
        )
        assert response is not None
        assert response.transactions is not None
