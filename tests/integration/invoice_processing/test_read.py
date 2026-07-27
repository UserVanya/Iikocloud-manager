"""Structure reads invoice_processing (test_server, write-стенд).

По одному list-вызову на каждый документный класс (10) + services (2)
+ counteragents. Проверка «ответ не None / items — список».

account/document transactions — skip, если нет account_id/document_id.

Запуск:
    uv run pytest tests/integration/invoice_processing/test_read.py -v -m test_server
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any
from uuid import UUID

import pytest
from iikocloud_client import (
    AccountTransactionsListRequest,
    DocumentTransactionsListRequest,
    GetCounteragentsRequest,
    ListRequest,
)
from iikocloud_client.exceptions import ApiException
from yaml import CSafeLoader
from yaml import load as yaml_load

from iikocloud import IikoCloudApiClientManager
from tests.integration.invoice_processing.conftest import call_with_429_retry

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]

_LIST_METHODS = [
    "list_inventory_incoming_invoices",
    "list_inventory_outgoing_invoices",
    "list_inventory_incoming_returned_invoices",
    "list_inventory_returned_invoices",
    "list_inventory_internal_transfers",
    "list_inventory_writeoff_documents",
    "list_inventory_production_documents",
    "list_inventory_disassemble_documents",
    "list_inventory_transformation_documents",
    "list_inventory_sales_documents",
    "list_finance_incoming_services",
    "list_finance_outgoing_services",
]


def _list_request(org_id: str) -> ListRequest:
    """ListRequest за последний год (все поля обязательны: from/organizationId/to)."""
    today = datetime.now(UTC).date()
    return ListRequest(
        var_from=(today - timedelta(days=365)).isoformat(),
        organization_id=org_id,
        to=today.isoformat(),
    )


@lru_cache
def _read_config_data(path: str) -> dict[str, Any]:
    """Прочитать и распарсить config.test.yml один раз на путь за процесс."""
    with open(path, "rb") as file:
        data: dict[str, Any] = yaml_load(file, Loader=CSafeLoader)
    return data


def _write_config_key(key: str) -> str | None:
    """Необязательный ключ из write-секции config.test.yml."""
    path = os.getenv("IIKOCLOUD_TEST_CONFIG")
    if not path:
        return None
    data = _read_config_data(path)
    value = (data.get("write") or {}).get(key)
    return str(value) if value else None


class TestInvoiceProcessingStructureReads:
    @pytest.mark.parametrize("method_name", _LIST_METHODS)
    async def test_list_documents(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        method_name: str,
    ) -> None:
        org_id = str(organization_id)  # invoice API: organizationId — строка
        method: Callable[..., Any] = getattr(manager, method_name)
        result = await call_with_429_retry(lambda: method(_list_request(org_id)))
        assert result is not None
        assert isinstance(result, list)

    async def test_get_counteragents(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        try:
            response = await manager.get_inventory_counteragents(
                GetCounteragentsRequest(
                    limit=1, offset=0, organization_id=str(organization_id)
                )
            )
        except ApiException as exc:
            if "EXTERNAL_SYSTEM_TIMEOUT" in str(exc.body or exc):
                pytest.skip(
                    "Стенд: counteragents — EXTERNAL_SYSTEM_TIMEOUT "
                    "(внешняя система стенда не отвечает)"
                )
            raise
        assert response is not None
        assert response.counteragents is not None

    async def test_list_finance_document_transactions(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        org_id = str(organization_id)
        invoices = await call_with_429_retry(
            lambda: manager.list_inventory_incoming_invoices(_list_request(org_id))
        )
        if not invoices:
            pytest.skip("Нет накладных на стенде — нечего брать как document_id")
        result = await call_with_429_retry(
            lambda: manager.list_finance_document_transactions(
                DocumentTransactionsListRequest(
                    document_id=invoices[0].document_id, organization_id=org_id
                )
            )
        )
        assert result is not None
        assert isinstance(result, list)

    async def test_list_finance_account_transactions(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        account_id = _write_config_key("account_id")
        if not account_id:
            pytest.skip("В write-секции config.test.yml не задан account_id")
        org_id = str(organization_id)
        today = datetime.now(UTC).date()
        result = await call_with_429_retry(
            lambda: manager.list_finance_account_transactions(
                AccountTransactionsListRequest(
                    account_id=account_id,
                    var_from=(today - timedelta(days=365)).isoformat(),
                    organization_id=org_id,
                    to=today.isoformat(),
                )
            )
        )
        assert result is not None
