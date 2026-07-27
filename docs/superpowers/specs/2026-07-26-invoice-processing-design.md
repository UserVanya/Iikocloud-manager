# Спека: блок Invoice Processing (16 классов)

Дата: 2026-07-26
Статус: утверждена (brainstorm с пользователем)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 16 классами Invoice Processing SDK (~90 методов).
Блочная спека и блочный план на весь блок (отклонение от правила
«1 класс = 1 спека», утверждено пользователем — 12 классов идентичны
по форме lifecycle).

### Auth (открытая точка мастер-спеки — закрыта)

Все 16 классов — тот же Bearer-токен и тот же хост
(`https://api-ru.iiko.services`), префиксы `/api/inventory/v1` и
`/api/finance/v1`. Отдельной авторизации нет, менеджер подходит как есть.

### Классы и методы

**Документные (inventory), lifecycle create/get/list/update/post/unpost/cancel:**
1. `disassemble_document` (7)
2. `incoming_invoices` (9: +`add_payment`, `set_payment_date`)
3. `incoming_returned_invoice` (7)
4. `internal_transfer` (7)
5. `outgoing_invoices` (10: +`add_payment`, `set_payment_date`,
   `calculate_cost_prices`)
6. `production_document` (7)
7. `returned_invoice` (7)
8. `sales_document` (7)
9. `transformation_document` (7)
10. `writeoff_document` (7)

**Финансовые (finance):**
11. `incoming_service` (7: create/get/list/update/post/unpost/cancel)
12. `outgoing_service` (7)

**Справочно-отчётные:**
13. `account_transactions.list` (read)
14. `document_transactions.list` (read)
15. `counteragents.get` (read, limit/offset 1..500 + type-фильтр)
16. `nomenclature.update_barcodes` (мутация)

Особенности:
- `organization_id` — **строка GUID (StrictStr), не UUID** (отличие от
  front-API); request-модель передаётся позиционным обязательным kwarg.
- `incoming_invoice` create обязательные: `counteragent`, `date`,
  `items[{amount, num, product, store}]`, `organization_id`.
- post — провести документ, unpost — распровести, cancel — пометить
  удалённым.

## 2. Структура пакета

Один пакет `iikocloud/mixins/invoice_processing/` с core-файлом на класс
(1 класс = 1 модуль внутри общего пакета):

```
invoice_processing/
  __init__.py          # реэкспорты всех mixins
  _shared.py           # общие типы/константы блока
  disassemble.py       # DisassembleCoreMixin
  incoming_invoices.py # IncomingInvoicesCoreMixin
  incoming_returned.py
  internal_transfer.py
  outgoing_invoices.py
  production.py
  returned.py
  sales.py
  transformation.py
  writeoff.py
  incoming_service.py
  outgoing_service.py
  references.py        # account_transactions, document_transactions,
                       # counteragents, nomenclature (4 маленьких класса)
  helpers.py           # InvoiceProcessingHelpersMixin (заготовка)
```

16 lazy-геттеров в `_base.py`, MRO-регистрация всех mixins в менеджере.

## 3. Rate limits

- Мутации (create/update/post/unpost/cancel/add_payment/
  set_payment_date/calculate_cost_prices/update_barcodes) — **100/60s**
- Read (get/list/account_transactions/document_transactions/
  counteragents) — **10/60s**

~90 значений `ApiMethod` (locked names = snake_case имён SDK-методов).

## 4. Helpers

Заготовка (решение пользователя).

## 5. Тесты

### Unit

Все ~90 методов: параметризованные таблицы по классам (делегирование,
точные kwargs/модели). organization_id — строка.

### Integration

**danger_write lifecycle на `incoming_invoice`** (write-стенд с учётом):
1. counteragent — из `counteragents.get` (справочник, limit=1,
   type=["supplier"]); skip, если контрагентов нет
2. store/product — из items существующей накладной
   (`list_incoming_invoices`, limit=1); skip, если накладных нет
   (справочных эндпоинтов для store/product в SDK нет)
3. `create_inventory_incoming_invoice` (минимальный документ) →
   `get_inventory_incoming_invoice` (читается) →
   `update_inventory_incoming_invoice` (коммент) →
   `post_inventory_incoming_invoice` →
   `unpost_inventory_incoming_invoice` →
   `cancel_inventory_incoming_invoice` в finally

**Structure-only** (`test_server`): list каждого документного класса
(10 вызовов), list services (2), account_transactions (нужен account_id
из существующего документа/списка — иначе skip), document_transactions,
counteragents (уже покрыт lifecycle'ом выше).

## 6. Открытые точки (решаются при реализации)

- Доступность `post/unpost` на стенде (закрытие периода в учёте может
  блокировать проведение — тогда skip с причиной, цикл укорачивается
  до create→get→update→cancel).
- Обязательность полей create на стенде сверх модели — по факту 400.

## 7. Definition of done

- ~90 core-обёрток в 16 core-файлах + helpers-заготовка, `ApiMethod`,
  лимиты, config.example.yml, MRO.
- Unit зелёные, ruff+mypy чистые.
- Integration: lifecycle incoming_invoice живьём (или skip с причиной),
  structure-only по остальным классам.
