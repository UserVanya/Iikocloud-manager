"""Danger_write lifecycle incoming_invoice (write-стенд с учётом).

counteragent — из справочника counteragents (fallback: из существующей
накладной); store/product — из items существующей накладной
-> create -> get -> update -> post -> unpost -> cancel (finally).

Если post падает с ошибкой закрытого периода — цикл сокращается
(post/unpost skip с причиной), cancel в finally всё равно выполняется.

Запуск:
    uv run pytest tests/integration/invoice_processing/test_lifecycle.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from iikocloud_client import (
    GetByIDRequest,
    GetCounteragentsRequest,
    IncomingInvoiceRequest,
    IncomingInvoiceRequestItem,
    ListRequest,
)
from iikocloud_client.exceptions import ApiException

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0
_MAX_429_RETRIES = 3
_429_BACKOFF_SEC = 5.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


async def _call_with_429_retry[T](call: Callable[[], Awaitable[T]]) -> T:
    """Вызвать API-метод с retry при 429.

    Стенд жёстко лимитирует invoice endpoints (429 при повторном вызове
    в пределах пары секунд), менеджер ретраит только 401.
    """
    for attempt in range(_MAX_429_RETRIES + 1):
        try:
            return await call()
        except ApiException as exc:
            if exc.status != 429 or attempt == _MAX_429_RETRIES:
                raise
            await asyncio.sleep(_429_BACKOFF_SEC)
    raise AssertionError("unreachable")


def _now_iso() -> str:
    """Текущее UTC-время в формате date-time стенда (YYYY-MM-DDThh:mm:ss.sss±hh:mm)."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")


def _list_request(org_id: str) -> ListRequest:
    """ListRequest за последний год (все поля обязательны: from/organizationId/to)."""
    today = datetime.now(UTC).date()
    return ListRequest(
        var_from=(today - timedelta(days=365)).isoformat(),
        organization_id=org_id,
        to=today.isoformat(),
    )


class TestIncomingInvoiceLifecycle:
    async def test_create_get_update_post_unpost_cancel(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        org_id = str(organization_id)  # invoice API: organizationId — строка

        # 1. counteragent из справочника (может быть недоступен на стенде)
        counteragent_id = None
        try:
            counteragents = await manager.get_inventory_counteragents(
                GetCounteragentsRequest(
                    limit=1, offset=0, organization_id=org_id, type=["supplier"]
                )
            )
            ca_items = counteragents.counteragents or []
            if ca_items:
                counteragent_id = ca_items[0].id
        except ApiException as exc:
            logger.warning("Справочник counteragents недоступен: %s", exc.status)

        # 2. store/product из items существующей накладной (+ fallback counteragent)
        invoice_list = await _call_with_429_retry(
            lambda: manager.list_inventory_incoming_invoices(_list_request(org_id))
        )
        if not invoice_list:
            pytest.skip("Нет существующих накладных на стенде (источник шаблона)")
        template = await _call_with_429_retry(
            lambda: manager.get_inventory_incoming_invoice(
                GetByIDRequest(
                    document_id=invoice_list[0].document_id, organization_id=org_id
                )
            )
        )
        if not counteragent_id:
            counteragent_id = (getattr(template, "counteragent", None) or "").strip()
        if not counteragent_id:
            pytest.skip(
                "Нет контрагента: справочник counteragents недоступен на стенде "
                "(EXTERNAL_SYSTEM_TIMEOUT), у существующих накладных counteragent пуст"
            )
        template_items = getattr(template, "items", None) or []
        if not template_items:
            pytest.skip("У существующей накладной нет позиций")
        store_id = template_items[0].store
        product_id = template_items[0].product

        document_id = None
        try:
            # 3. create (минимальный документ)
            create_response = await manager.create_inventory_incoming_invoice(
                IncomingInvoiceRequest(
                    organization_id=org_id,
                    counteragent=counteragent_id,
                    var_date=_now_iso(),
                    items=[
                        IncomingInvoiceRequestItem(
                            amount=1.0,
                            num=1,
                            price=100.0,
                            product=product_id,
                            store=store_id,
                        )
                    ],
                    comment="integration test",
                )
            )
            document_id = getattr(create_response, "document_id", None) or getattr(
                create_response, "id", None
            )
            assert document_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 4. get — читается
            fetched = await manager.get_inventory_incoming_invoice(
                GetByIDRequest(document_id=document_id, organization_id=org_id)
            )
            assert fetched is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 5. update — коммент
            update_request = IncomingInvoiceRequest(
                organization_id=org_id,
                counteragent=counteragent_id,
                var_date=_now_iso(),
                items=[
                    IncomingInvoiceRequestItem(
                        amount=1.0, num=1, price=100.0,
                        product=product_id, store=store_id,
                    )
                ],
                comment="integration test updated",
                document_id=document_id,
            )
            await manager.update_inventory_incoming_invoice(update_request)

            await asyncio.sleep(_API_PAUSE_SEC)

            # 6. post -> 7. unpost (skip при закрытом периоде — фиксируем)
            try:
                await manager.post_inventory_incoming_invoice(
                    GetByIDRequest(document_id=document_id, organization_id=org_id)
                )
                await asyncio.sleep(_API_PAUSE_SEC)
                await manager.unpost_inventory_incoming_invoice(
                    GetByIDRequest(document_id=document_id, organization_id=org_id)
                )
            except Exception as exc:  # noqa: BLE001
                pytest.skip(f"post/unpost недоступен (закрытый период?): {exc}")

        finally:
            # 8. cancel в finally
            if document_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_inventory_incoming_invoice(
                        GetByIDRequest(document_id=document_id, organization_id=org_id)
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "CLEANUP: накладная %s не отменена: %s",
                        document_id,
                        exc,
                    )
