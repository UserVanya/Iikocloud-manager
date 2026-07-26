# Спека: модуль report

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч «прочее»)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над обоими методами `ReportApi` SDK (оба read-only).

### Методы и лимиты

| Метод | Endpoint | Лимит |
|---|---|---|
| `get_customer_transactions_by_date` | `/api/1/loyalty/iiko/customer/transactions/by_date` | 10/60s |
| `get_customer_transactions_by_revision` | `/api/1/loyalty/iiko/customer/transactions/by_revision` | 10/60s |

Особенности:
- `by_date` — постраничная (page_number/page_size, даты UTC включительно,
  формат `yyyy-MM-dd HH:mm:ss.fff`).
- `by_revision` — инкрементальная (revision / lastTransactionId; ответ
  несёт last_revision/last_transaction_id для следующего запроса).
- `TransactionType` — int-enum без имён (семантика — по доке iiko).

## 2. Helpers

Заготовка (решение батча).

## 3. Файловая структура

- `iikocloud/mixins/report/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_report_api`, 2 `ApiMethod`, 2 поля
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 2 лимита
- Тесты: `tests/unit/test_report.py`,
  `tests/integration/customers/test_transactions.py`

## 4. Тесты

### Unit

Оба метода: делегирование, проксирование ответа.

### Integration (`test_server`, write-секция)

- `get_customer_transactions_by_date` (page_size=10, диапазон — последние
  30 дней, customer_id — несуществующий UUID: валидная структура, список
  может быть пуст).
- `get_customer_transactions_by_revision` (page_size=10, тот же customer) —
  структура (last_revision/page_size/transactions).
- Бонус, если легко: транзакции реального клиента из write-стенда
  (в прошлых тестах были top_up/withdraw) — не требуем, только структура.

## 5. Definition of done

- 2 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
