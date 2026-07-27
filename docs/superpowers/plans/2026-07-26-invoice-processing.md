# Invoice Processing Block Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Обёртки над всеми 93 методами 16 классов Invoice Processing + unit- и integration-тесты (lifecycle incoming_invoice + structure reads).

**Architecture:** Один пакет `iikocloud/mixins/invoice_processing/` с core-файлом на класс (шаблон идентичен существующим доменам: inner `api_call` → lazy getter → `execute_with_retry`). organization_id — **строка GUID** (не UUID) во всех моделях блока.

**Spec:** `docs/superpowers/specs/2026-07-26-invoice-processing-design.md`

## Global Constraints

- Core-метод принимает SDK request-модель, возвращает SDK response.
- Locked Names: `ApiMethod` value == snake_case SDK method == поле в settings/dataclass.
- Лимиты: мутации (create/update/post/unpost/cancel/add_payment/set_payment_date/calculate_cost_prices/update_barcodes) — 100/60s; read (get/list/account_transactions/document_transactions/counteragents) — 10/60s.
- organization_id в моделях блока — `StrictStr` (GUID-строка), НЕ UUID.
- Гейты: `.venv/bin/python -m pytest tests/unit -q`, `.venv/bin/ruff check .`, `.venv/bin/python -m mypy iikocloud tests`.

## Единый шаблон core-метода (для всех 93)

```python
    async def <method>(
        self,
        request: <RequestModel>,
    ) -> <ResponseModel>:
        """<одна строка смысла>."""

        async def api_call() -> <ResponseModel>:
            api = await self.get_<api_slot>()
            return await api.<method>(<kwarg>=request)

        return await self.execute_with_retry(ApiMethod.<ENUM>, api_call)
```

## Таблица методов (method | kwarg | request-model | response-model | лимит)

Извлечено интроспекцией из SDK 2026-07-26. Lazy-геттеры: `get_<snake>_api` по имени класса (напр. `get_disassemble_document_api`). Классы API-клиентов: `PublicApiInvoiceProcessing<Entity>Api`.

### disassemble_document (7)
create → `disassemble_document_create_request` / DisassembleDocumentCreateRequest / DisassembleDocumentSaveResponse / 100
get → `get_by_id_request` / GetByIDRequest / DisassembleDocumentGetResponse / 10
list → `list_request` / ListRequest / List[DisassembleDocumentListItem] / 10
update → `disassemble_document_update_request` / DisassembleDocumentUpdateRequest / DisassembleDocumentSaveResponse / 100
post/unpost/cancel → `get_by_id_request` / GetByIDRequest / DisassembleDocumentSaveResponse / 100

### incoming_invoices (9)
create/update → `incoming_invoice_request` / IncomingInvoiceRequest / IncomingInvoiceSaveResponse / 100
get → `get_by_id_request` / GetByIDRequest / IncomingInvoice / 10
list → `list_request` / ListRequest / List[IncomingInvoiceListItem] / 10
post/unpost/cancel → `get_by_id_request` / IncomingInvoiceSaveResponse / 100
add_payment → `pay_request` / PayRequest / AccountingTransactionUserResponse / 100
set_payment_date → `set_payment_date_request` / SetPaymentDateRequest / SetPaymentDateResponse / 100

### incoming_returned_invoice (7)
create → `incoming_returned_invoice_create_request` / IncomingReturnedInvoiceCreateRequest / IncomingReturnedInvoiceSaveResponse / 100
update → `incoming_returned_invoice_update_request` / IncomingReturnedInvoiceUpdateRequest / IncomingReturnedInvoiceSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / IncomingReturnedInvoiceSaveResponse (get → IncomingReturnedInvoiceGetResponse) / 100 (get / 10)
list → `list_request` / List[IncomingReturnedInvoiceListItem] / 10

### internal_transfer (7)
create → `internal_transfer_create_request` / InternalTransferCreateRequest / InternalTransferSaveResponse / 100
update → `internal_transfer_update_request` / InternalTransferUpdateRequest / InternalTransferSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / InternalTransferSaveResponse (get → InternalTransferGetResponse) / 100 (get / 10)
list → `list_request` / List[InternalTransferListItem] / 10

### outgoing_invoices (10)
create/update → `outgoing_invoice_request` / OutgoingInvoiceRequest / OutgoingInvoiceSaveResponse / 100
get → `get_by_id_request` / OutgoingInvoice / 10
list → `list_request` / List[OutgoingInvoiceListItem] / 10
post/unpost/cancel → `get_by_id_request` / OutgoingInvoiceSaveResponse / 100
add_payment → `pay_outgoing_invoice_request` / PayOutgoingInvoiceRequest / AccountingTransactionUserResponse / 100
set_payment_date → `set_payment_date_outgoing_request` / SetPaymentDateOutgoingRequest / SetPaymentDateOutgoingResponse / 100
calculate_cost_prices → `get_cost_prices_request` / GetCostPricesRequest / GetCostPricesResponse / 100

### production_document (7)
create → `production_document_create_request` / ProductionDocumentCreateRequest / ProductionDocumentSaveResponse / 100
update → `production_document_update_request` / ProductionDocumentUpdateRequest / ProductionDocumentSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / ProductionDocumentSaveResponse (get → ProductionDocumentGetResponse) / 100 (get / 10)
list → `list_request` / List[ProductionDocumentListItem] / 10

### returned_invoice (7)
create → `returned_invoice_create_request` / ReturnedInvoiceCreateRequest / ReturnedInvoiceSaveResponse / 100
update → `returned_invoice_update_request` / ReturnedInvoiceUpdateRequest / ReturnedInvoiceSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / ReturnedInvoiceSaveResponse (get → ReturnedInvoiceGetResponse) / 100 (get / 10)
list → `list_request` / List[ReturnedInvoiceListItem] / 10

### sales_document (7)
create → `sales_document_create_request` / SalesDocumentCreateRequest / SalesDocumentSaveResponse / 100
update → `sales_document_update_request` / SalesDocumentUpdateRequest / SalesDocumentSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / SalesDocumentSaveResponse (get → SalesDocumentGetResponse) / 100 (get / 10)
list → `list_request` / List[SalesDocumentListItem] / 10

### transformation_document (7)
create → `transformation_document_create_request` / TransformationDocumentCreateRequest / TransformationDocumentSaveResponse / 100
update → `transformation_document_update_request` / TransformationDocumentUpdateRequest / TransformationDocumentSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / TransformationDocumentSaveResponse (get → TransformationDocumentGetResponse) / 100 (get / 10)
list → `list_request` / List[TransformationDocumentListItem] / 10

### writeoff_document (7)
create → `writeoff_document_create_request` / WriteoffDocumentCreateRequest / WriteoffDocumentSaveResponse / 100
update → `writeoff_document_update_request` / WriteoffDocumentUpdateRequest / WriteoffDocumentSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / WriteoffDocumentSaveResponse (get → WriteoffDocumentGetResponse) / 100 (get / 10)
list → `list_request` / List[WriteoffDocumentListItem] / 10

### incoming_service (7)
create → `incoming_service_create_request` / IncomingServiceCreateRequest / IncomingServiceSaveResponse / 100
update → `incoming_service_update_request` / IncomingServiceUpdateRequest / IncomingServiceSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / IncomingServiceSaveResponse (get → IncomingServiceGetResponse) / 100 (get / 10)
list → `list_request` / List[IncomingServiceListItem] / 10

### outgoing_service (7)
create → `outgoing_service_create_request` / OutgoingServiceCreateRequest / OutgoingServiceSaveResponse / 100
update → `outgoing_service_update_request` / OutgoingServiceUpdateRequest / OutgoingServiceSaveResponse / 100
get/post/unpost/cancel → `get_by_id_request` / OutgoingServiceSaveResponse (get → OutgoingServiceGetResponse) / 100 (get / 10)
list → `list_request` / List[OutgoingServiceListItem] / 10

### references (4 класса, 4 метода)
- `list_finance_account_transactions` → `account_transactions_list_request` / AccountTransactionsListRequest / AccountTransactionsResponse / 10
- `list_finance_document_transactions` → `document_transactions_list_request` / DocumentTransactionsListRequest / List[DocumentTransactionItem] / 10
- `get_inventory_counteragents` → `get_counteragents_request` / GetCounteragentsRequest / GetCounteragentsResponse / 10
- `update_inventory_product_barcodes` → `update_product_barcodes_request` / UpdateProductBarcodesRequest / UpdateProductBarcodesResponse / 100

Примечание: точные имена *ListItem-моделей для list-ответов — уточнить по SDK при реализации (аннотация `List[...]`); если ListItem-класс называется иначе — использовать фактический. Тип возврата в обёртке — `list[<ItemModel>]` или точный generic SDK.

---

### Task 1: Инфраструктура (16 lazy-геттеров, 93 ApiMethod, лимиты)

**Files:**
- Modify: `iikocloud/mixins/_base.py` (импорты 16 API-классов, ApiMethod +93, MethodRateLimits +93, слоты +16, геттеры +16)
- Modify: `iikocloud/api_client_manager.py` (слоты +16 в `__init__`, импорты)
- Modify: `iikocloud/config_reader.py` (+93 поля)
- Modify: `config.example.yml` (+93 блока)
- Test: `tests/unit/test_config_reader.py`

**Interfaces:**
- Produces: 93 `ApiMethod` значений (locked names из таблиц выше); 16 геттеров `get_<snake>_api()` для классов `PublicApiInvoiceProcessing<Entity>Api`.

Имена слотов/геттеров (16): `disassemble_document`, `incoming_invoices`, `incoming_returned_invoice`, `internal_transfer`, `outgoing_invoices`, `production_document`, `returned_invoice`, `sales_document`, `transformation_document`, `writeoff_document`, `incoming_service`, `outgoing_service`, `account_transactions`, `document_transactions`, `counteragents`, `nomenclature` (invoice-номенклатура! конфликт имён с menu-доменом отсутствует: слот `_invoice_nomenclature_api`, геттер `get_invoice_nomenclature_api`).

ВНИМАНИЕ: геттеры возвращают классы с длинными именами `PublicApiInvoiceProcessing<Entity>Api` — импорты в `_base.py` и `api_client_manager.py` через `from iikocloud_client import (...)` с комментарием `# Invoice Processing`.

- [ ] **Step 1: Failing test — все 93 locked names**

В `tests/unit/test_config_reader.py`:

```python
def test_invoice_processing_methods_have_limits() -> None:
    """93 метода invoice processing есть в ApiMethod и MethodRateLimits."""
    from iikocloud.mixins._base import ApiMethod, MethodRateLimits

    read_names = [
        # get/list документных классов + references — 10/60s
        "list_finance_account_transactions",
        "list_finance_document_transactions",
        "get_inventory_counteragents",
        # ... сюда все get_inventory_* и list_inventory_* имена из таблиц плана
    ]
    mutation_names = [
        # create/update/post/unpost/cancel/add_payment/set_payment_date/
        # calculate_cost_prices/update_barcodes — 100/60s
        # ... сюда все остальные имена из таблиц плана
    ]
    limits = MethodRateLimits.from_settings(MethodRateLimitsSettings())
    for name in read_names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(10 / 60.0)
    for name in mutation_names:
        config = limits.for_method(ApiMethod(name))
        assert config.max_requests / config.time_window_seconds == pytest.approx(100 / 60.0)
    # страховка от пропуска: ровно 93 метода
    assert len(read_names) + len(mutation_names) == 93
```

Реализатору: заполнить `read_names` и `mutation_names` ТОЛЬКО копипастой имён методов из колонки method таблиц плана (get/list/references → read, остальные → mutation). Имена по паттерну не выдумывать — list-имена нерегулярны (`list_inventory_internal_transfers`, `list_inventory_incoming_returned_invoices` и т.п.).

- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — все 93 значений в `ApiMethod` (секция `# Invoice Processing` с подкомментариями по сущностям), 93 поля `RateLimitConfig`, 93 поля settings (100/60 или 10/60 по таблицам), 16 слотов + 16 геттеров, импорты 16 классов в обоих файлах, 93 блока в `config.example.yml`.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat: register rate limits and lazy clients for invoice processing`

---

### Task 2: Core — счета (incoming/outgoing invoices + returned invoice payments)

**Files:**
- Create: `iikocloud/mixins/invoice_processing/__init__.py`
- Create: `iikocloud/mixins/invoice_processing/incoming_invoices.py`
- Create: `iikocloud/mixins/invoice_processing/outgoing_invoices.py`
- Test: `tests/unit/test_invoice_processing_invoices.py`

**Interfaces:**
- Produces: `IncomingInvoicesCoreMixin` (9), `OutgoingInvoicesCoreMixin` (10) по таблицам

- [ ] **Step 1: Failing tests** — параметризованные таблицы по обеим сущностям (шаблон `tests/unit/test_employees.py`): 19 методов, модели из таблиц; organization_id в моделях — СТРОКА (`"00000000-0000-0000-0000-000000000001"`), не UUID.
- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — 2 core-файла по единому шаблону. `__init__.py` пока реэкспортирует созданное.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat(invoice-processing): incoming/outgoing invoices wrappers`

---

### Task 3: Core — документы группа A (disassemble, production, transformation, writeoff)

**Files:**
- Create: `iikocloud/mixins/invoice_processing/{disassemble,production,transformation,writeoff}.py`
- Test: `tests/unit/test_invoice_processing_docs_a.py`

- [ ] **Step 1: Failing tests** — 4 таблицы × 7 методов.
- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — 4 core-файла по шаблону; `__init__.py` дополнен.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat(invoice-processing): disassemble/production/transformation/writeoff wrappers`

---

### Task 4: Core — документы группа B (incoming_returned, internal_transfer, returned, sales) + services

**Files:**
- Create: `iikocloud/mixins/invoice_processing/{incoming_returned,internal_transfer,returned,sales,incoming_service,outgoing_service}.py`
- Test: `tests/unit/test_invoice_processing_docs_b.py`

- [ ] **Step 1: Failing tests** — 6 таблиц × 7 методов (42).
- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — 6 core-файлов; `__init__.py` дополнен.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat(invoice-processing): returned/transfer/sales/services wrappers`

---

### Task 5: References + helpers-заготовка + полная MRO-регистрация

**Files:**
- Create: `iikocloud/mixins/invoice_processing/references.py` (4 core-миксина: `AccountTransactionsCoreMixin`, `DocumentTransactionsCoreMixin`, `CounteragentsCoreMixin`, `InvoiceNomenclatureCoreMixin`)
- Create: `iikocloud/mixins/invoice_processing/helpers.py` (`InvoiceProcessingHelpersMixin` — наследует ВСЕ 16 core-миксинов; заготовка)
- Modify: `iikocloud/api_client_manager.py` (импорт + MRO + docstring)
- Test: `tests/unit/test_invoice_processing_references.py`

**Interfaces:**
- Produces: 4 reference-обёртки; `InvoiceProcessingHelpersMixin` как единая точка входа блока в MRO

ВНИМАНИЕ: `InvoiceProcessingHelpersMixin` наследует 16 core-миксинов — проверить отсутствие конфликтов имён методов между ними (их нет: имена методов уникальны по locked names). Порядок наследования — по алфавиту сущностей, с комментарием.

- [ ] **Step 1: Failing tests** — таблица 4 методов.
- [ ] **Step 2: Run — FAIL**
- [ ] **Step 3: Реализация** — references.py, helpers.py, финальный `__init__.py` (все реэкспорты), MRO.
- [ ] **Step 4: Run — PASS + гейты**
- [ ] **Step 5: Commit** `feat(invoice-processing): references and full manager registration`

---

### Task 6: Integration — lifecycle incoming_invoice + structure reads

**Files:**
- Create: `tests/integration/invoice_processing/{__init__,test_lifecycle.py,test_read.py}`

**Interfaces:**
- Consumes: фикстуры `manager`, `organization_id`

- [ ] **Step 1: Lifecycle (danger_write)**

`tests/integration/invoice_processing/test_lifecycle.py`:

```python
"""Danger_write lifecycle incoming_invoice (write-стенд с учётом).

counteragent (справочник) + store/product (items существующей накладной)
-> create -> get -> update -> post -> unpost -> cancel (finally).

Запуск:
    uv run pytest tests/integration/invoice_processing/test_lifecycle.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    GetByIDRequest,
    GetCounteragentsRequest,
    IncomingInvoiceRequest,
    IncomingInvoiceRequestItem,
    ListRequest,
)

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestIncomingInvoiceLifecycle:
    async def test_create_get_update_post_unpost_cancel(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        org_id = str(organization_id)  # invoice API: organizationId — строка

        # 1. counteragent из справочника
        counteragents = await manager.get_inventory_counteragents(
            GetCounteragentsRequest(limit=1, type=["supplier"])
        )
        items = getattr(counteragents, "counteragents", None) or []
        if not items:
            pytest.skip("Нет контрагентов-поставщиков на стенде")
        counteragent_id = items[0].id

        # 2. store/product из items существующей накладной
        invoices = await manager.list_inventory_incoming_invoices(
            ListRequest(organization_id=org_id, limit=1)
        )
        invoice_list = getattr(invoices, "items", invoices) or []
        if not invoice_list:
            pytest.skip("Нет существующих накладных на стенде (источник store/product)")
        template = await manager.get_inventory_incoming_invoice(
            GetByIDRequest(id=invoice_list[0].id, organization_id=org_id)
        )
        template_items = getattr(template, "items", None) or []
        if not template_items:
            pytest.skip("У существующей накладной нет позиций")
        store_id = template_items[0].store
        product_id = template_items[0].product

        document_id = None
        try:
            # 3. create (минимальный документ)
            from datetime import datetime

            create_response = await manager.create_inventory_incoming_invoice(
                IncomingInvoiceRequest(
                    organization_id=org_id,
                    counteragent=counteragent_id,
                    var_date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+00:00"),
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
                GetByIDRequest(id=document_id, organization_id=org_id)
            )
            assert fetched is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 5. update — коммент
            update_request = IncomingInvoiceRequest(
                organization_id=org_id,
                counteragent=counteragent_id,
                var_date=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+00:00"),
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
            await manager.post_inventory_incoming_invoice(
                GetByIDRequest(id=document_id, organization_id=org_id)
            )
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.unpost_inventory_incoming_invoice(
                GetByIDRequest(id=document_id, organization_id=org_id)
            )

        finally:
            # 8. cancel в finally
            if document_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_inventory_incoming_invoice(
                        GetByIDRequest(id=document_id, organization_id=org_id)
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "CLEANUP: накладная %s не отменена: %s",
                        document_id,
                        exc,
                    )
```

ВНИМАНИЕ реализатору: точные поля id у моделей (`document_id`/`id`, поле списка `items`) и формат даты — сверить по SDK/ответам стенда на первом прогоне; если post падает с ошибкой закрытого периода — сократить цикл (skip post/unpost с записью причины в отчёте).

- [ ] **Step 2: Structure reads (`test_server`)**

`tests/integration/invoice_processing/test_read.py` — по одному list-вызову на каждый документный класс (10) + services (2) + counteragents; organization_id=str(...); проверка «ответ не None / items не None». account/document transactions — пропустить, если нет account_id (skip).

- [ ] **Step 3: Прогон живьём** — `timeout 900 bash -c 'IIKOCLOUD_TEST_CONFIG=config.test.yml .venv/bin/python -m pytest tests/integration/invoice_processing -q -rs'`
- [ ] **Step 4: Регрессия + гейты**
- [ ] **Step 5: Commit** `test: invoice processing lifecycle and structure reads`
