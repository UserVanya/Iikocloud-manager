# Спека: модуль deliveries_retrieve

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 6 методами `DeliveriesRetrieveApi` SDK (deprecated-методов
в классе нет). Все методы read-only (POST, restriction group
`Orders: receiving`; у `by_revision` — `Orders: receiving by revision`).

### Методы

| Метод | Endpoint | Request → Response |
|---|---|---|
| `get_deliveries_by_delivery_date_and_phone` | `/api/1/deliveries/by_delivery_date_and_phone` | `OrdersByDeliveryDateAndPhoneRequest` → `OrdersWithRevisionResponse` |
| `get_deliveries_by_delivery_date_and_status` | `/api/1/deliveries/by_delivery_date_and_status` | `OrdersByDeliveryDateAndStatusRequest` → `OrdersWithRevisionResponse` |
| `get_deliveries_by_id` | `/api/1/deliveries/by_id` | `OrdersByIdRequest` → `OrdersResponse` |
| `get_deliveries_by_revision` | `/api/1/deliveries/by_revision` | `OrdersByRevisionRequest` → `OrdersWithRevisionResponse` |
| `get_delivery_history_by_delivery_date_and_phone` | `/api/1/deliveries/history/by_delivery_date_and_phone` | `OrdersHistoryByDeliveryDateAndPhoneRequest` → `OrdersWithRevisionResponse` |
| `search_deliveries` | `/api/1/deliveries/by_delivery_date_and_source_key_and_filter` | `OrdersByDeliveryDateAndFilterRequest` → `OrdersWithRevisionResponse` |

Особенности домена:
- «Горячие» заказы — последние 7 дней; история — 90 дней; revision-окно —
  3 часа (серверные ограничения, задокументировать в docstring'ах).
- `organization_ids` — список везде, кроме `by_id` (одиночный).
- Ответы: `OrdersWithRevisionResponse` (correlation_id, max_revision,
  orders_by_organizations) у 5 методов; плоский `OrdersResponse` — у `by_id`.
- Пагинации нет; инкрементальная синхронизация через start_revision/max_revision.

## 2. Валидация на нашей стороне (ValueError до вызова SDK)

- `get_deliveries_by_id`:
  - `order_ids` и `pos_order_ids` одновременно заданы → ValueError (XOR);
  - оба списка пусты/None → ValueError;
  - len > 200 в любом из списков → ValueError.
- `get_delivery_history_by_delivery_date_and_phone`:
  - `rows_count > 200` или `< 1` → ValueError.

## 3. Helpers (решение пользователя — пишем)

- `get_delivery_by_id(organization_id, order_id) -> OrderInfo | None` —
  короткая форма: одиночный заказ из плоского `OrdersResponse.orders`
  (None, если не найден). Используется и для read-back в тестах.
- `get_customer_deliveries(organization_ids, phone, days=7)
  -> list[OrderInfo]` — заказы клиента по телефону за последние N дней:
  сборка `delivery_date_from/to` (формат `yyyy-MM-dd HH:mm:ss.fff`,
  локальное время терминала) + вызов
  `get_deliveries_by_delivery_date_and_phone`, выравнивание
  `orders_by_organizations` в плоский список.

## 4. Файловая структура

- `iikocloud/mixins/deliveries_retrieve/__init__.py` — реэкспорты (конвенция)
- `iikocloud/mixins/deliveries_retrieve/core.py` — `DeliveriesRetrieveCoreMixin`
- `iikocloud/mixins/deliveries_retrieve/helpers.py` —
  `DeliveriesRetrieveHelpersMixin`
- `iikocloud/mixins/_base.py` — lazy-геттер `get_deliveries_retrieve_api`,
  6 значений `ApiMethod`, 6 полей `MethodRateLimits`
- `iikocloud/api_client_manager.py` — слот в `__init__`, MRO, docstring
- `iikocloud/config_reader.py` + `config.example.yml` — 6 лимитов
- Тесты: `tests/unit/test_deliveries_retrieve.py`,
  `tests/integration/deliveries/test_read.py` (read-back),
  `tests/integration/deliveries/test_read_structure.py` (structure-only)

## 5. Rate limits

Все 6 методов — **10 / 60 s** (read-запросы, схема A').

## 6. Тесты

### Unit (моки SDK)

Все 6 core-методов: делегирование, проксирование ответа. Валидация:
все ветки ValueError из §2 (SDK не вызывается). Helpers: сборка запросов
(даты, XOR-логика), выравнивание списка, None для ненайденного заказа.

### Integration

**Read-back danger_write** (`tests/integration/deliveries/test_read.py`,
маркер `danger_write`):
1. create заказа (как в `test_write.py`: реальный продукт, тестовый
   телефон, `DeliveryByClient`, гард на is_alive)
2. `get_delivery_by_id` находит заказ (id совпадает, phone совпадает)
3. `search_deliveries` по тому же телефону находит заказ
4. cancel в finally

**Structure-only** (`tests/integration/deliveries/test_read_structure.py`,
маркер `test_server` — read-тесты на write-секции):
- `get_deliveries_by_delivery_date_and_phone` (delivery_date_from = сейчас
  минус 1 день)
- `get_deliveries_by_delivery_date_and_status` (statuses=[Cancelled])
- `get_deliveries_by_revision` (start_revision=0 или текущая минус окно —
  уточнить поведение стенда при реализации)
- `get_delivery_history_by_delivery_date_and_phone` (rows_count=10,
  тестовый телефон)
Проверки: correlation_id + валидная структура ответа (списки могут быть
пустыми — без привязки к данным).

## 7. Открытые точки (решаются при реализации)

- Поведение `get_deliveries_by_revision` при start_revision=0 на стенде
  (может вернуть ошибку окна 3 часа — тогда skip/skip-вариант с текущей
  ревизией из max_revision первого вызова).
- Задержка индексации: свежесозданный заказ может быть виден в
  retrieve-методах не мгновенно — при флаки добавить bounded-поллинг
  (как в wallet/stop-list тестах).

## 8. Definition of done

- 6 core + 2 helpers, валидация из §2, `ApiMethod`, rate limits,
  config.example.yml, регистрация в менеджере.
- Unit зелёные (включая существующие 121), ruff+mypy чистые.
- Integration: read-back и structure-only прогнаны живьём (или skip
  с зафиксированной причиной).
