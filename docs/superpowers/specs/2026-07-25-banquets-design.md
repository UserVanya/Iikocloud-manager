# Спека: модуль banquets_reserves

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч «прочее»)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 12 методами `BanquetsReservesApi` SDK (deprecated нет).

### Методы и лимиты

Read (20/60s — решение пользователя):

| Метод | Endpoint |
|---|---|
| `get_reserve_available_organizations` | `/api/1/reserve/available_organizations` |
| `get_reserve_terminal_groups` | `/api/1/reserve/available_terminal_groups` |
| `get_reserve_restaurant_sections` | `/api/1/reserve/available_restaurant_sections` |
| `get_reserve_statuses_by_id` | `/api/1/reserve/status_by_id` |
| `get_restaurant_sections_workload` | `/api/1/reserve/restaurant_sections_workload` |

Мутации:

| Метод | Endpoint | Лимит |
|---|---|---|
| `create_reserve` | `/api/1/reserve/create` | 20/60s |
| `add_banquet_order_items` | `/api/1/reserve/add_items` | 100/60s |
| `add_banquet_order_payments` | `/api/1/reserve/add_payments` | 100/60s |
| `cancel_reserve` | `/api/1/reserve/cancel` | 100/60s |
| `change_banquet_order_items` | `/api/1/reserve/change_items` | 100/60s |
| `change_reserve_estimated_start_time` | `/api/1/reserve/change_estimated_start_time` | 100/60s |
| `change_reserve_tables` | `/api/1/reserve/change_tables` | 100/60s |

Особенности:
- `create_reserve` обязательные: phone (+, ≥8 цифр), customer
  (DeliveryOrderCreateRegularCustomer), estimatedStartTime (≤90 дней),
  durationInMinutes, shouldRemind, tableIds. Ответ `ReserveResponse`
  (reserve_info с creation_status).
- `cancel_reserve` — только для резервов в статусе New;
  `cancel_reason: ReserveCancelReason` (ClientRefused и т.п.).
- `get_reserve_restaurant_sections` — источник tableIds для будущего
  OrdersApi (без organizationId, фильтр по terminalGroupIds).

## 2. Helpers

Заготовка (решение батча).

## 3. Файловая структура

- `iikocloud/mixins/banquets/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_banquets_reserves_api`, 12 `ApiMethod`,
  12 полей
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 12 лимитов
- Тесты: `tests/unit/test_banquets.py`,
  `tests/integration/banquets/{__init__,test_read.py,test_reserve.py}`

## 4. Тесты

### Unit

Все 12 методов: делегирование, проксирование ответа.

### Integration

- Structure-only (`test_server`): available_organizations,
  reserve_terminal_groups, restaurant_sections (по terminal group стенда),
  sections_workload (date_from — сегодня).
- danger_write (reserve lifecycle):
  sections → первый столик (skip, если секций/столиков нет) →
  `create_reserve` (тестовый телефон, customer name, estimatedStartTime =
  завтра +1ч, duration 60, shouldRemind=False, гард на живой фронт) →
  `get_reserve_statuses_by_id` (резерв читается, статус New) →
  `cancel_reserve` (ClientRefused) в finally.

## 5. Definition of done

- 12 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
