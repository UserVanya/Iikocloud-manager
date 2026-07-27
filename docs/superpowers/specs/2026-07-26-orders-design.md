# Спека: модуль orders (столовые заказы)

Дата: 2026-07-26
Статус: утверждена (brainstorm с пользователем)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 12 методами `OrdersApi` SDK (deprecated нет).

### Методы и лимиты

| Метод | Endpoint | Лимит |
|---|---|---|
| `create_table_order` | `/api/1/order/create` | 20/60s |
| `add_customer_to_table_order` | `/api/1/order/add_customer` | 100/60s |
| `add_items_to_table_order` | `/api/1/order/add_items` | 100/60s |
| `add_table_order_payments` | `/api/1/order/add_payments` | 100/60s |
| `change_table_order_payments` | `/api/1/order/change_payments` | 100/60s |
| `change_table_order_external_data` | `/api/1/order/change_external_data` | 100/60s |
| `close_table_order` | `/api/1/order/close` | 100/60s |
| `cancel_table_order` | `/api/1/order/cancel` | 100/60s |
| `initialize_table_orders_by_pos_orders` | `/api/1/order/init_by_posOrder` | 100/60s |
| `initialize_table_orders_by_tables` | `/api/1/order/init_by_table` | 100/60s |
| `get_table_orders_by_id` | `/api/1/order/by_id` | 20/60s |
| `get_table_orders_by_table` | `/api/1/order/by_table` | 20/60s |

Особенности:
- `create_table_order` обязательные: `organization_id`, `terminal_group_id`,
  `order.items`. Ответ `TableOrderResponse` (order_info.creation_status).
- `cancel_table_order` — только с iiko 9.0.5; на старых стендах —
  `close_table_order`.
- `change_table_order_payments` падает при processed-платежах (полная замена).
- `get_table_orders_by_id`: order_ids XOR pos_order_ids, organization_ids —
  список. `get_table_orders_by_table`: история 90 дней, статусы
  New/Bill/Closed/Deleted.
- Kwarg-ловушки: `add_table_order_payments` → `add_order_payments_request`,
  `change_table_order_external_data` → `change_external_data_request`,
  `change_table_order_payments` → `change_payments_request`.

## 2. Helpers

Заготовка (решение пользователя). Позиции — через существующие
`build_product_item`/`build_compound_item`.

## 3. Файловая структура

- `iikocloud/mixins/orders/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_orders_api`, 12 `ApiMethod`, 12 полей
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 12 лимитов
- Тесты: `tests/unit/test_orders.py`,
  `tests/integration/orders/{__init__,test_read.py,test_lifecycle.py}`

## 4. Тесты

### Unit

Все 12 методов: делегирование, точные kwargs (включая 3 ловушки).

### Integration

- Structure-only (`test_server`): `get_table_orders_by_id` (по фейковому id),
  `get_table_orders_by_table` (по столику стенда из sections).
- danger_write lifecycle:
  1. sections → столик (skip, если нет)
  2. `create_table_order` (1 продукт через `build_product_item`, гард на
     живой фронт) — `creation_status != Error`
  3. `get_table_orders_by_id` — заказ читается
  4. `add_items_to_table_order` — correlation_id
  5. `get_table_orders_by_table` — заказ висит на столике
  6. Cleanup в finally: `cancel_table_order`; при 400 с признаком версии
     (<9.0.5 / метод недоступен) — fallback `close_table_order`;
     при неудаче обоих — error-лог (заказ остаётся на столике стенда,
     фиксируем в отчёте).

## 5. Открытые точки (решаются при реализации)

- Версия iiko стенда (≥9.0.5 для cancel) — детект по факту ошибки.
- Обязательность `order_type_id`/`payments` на стенде для create —
  по факту 400 добавить минимум (как с drafts/service_type).

## 6. Definition of done

- 12 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
