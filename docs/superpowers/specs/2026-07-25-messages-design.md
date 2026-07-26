# Спека: модуль messages

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч «прочее»)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 4 методами `MessagesApi` SDK (deprecated нет).

### Методы и лимиты

| Метод | Endpoint | Лимит |
|---|---|---|
| `check_sms_sending_possibility` | `/api/1/loyalty/iiko/check_sms_sending_possibility` | 10/60s |
| `check_sms_status` | `/api/1/loyalty/iiko/check_sms_status` | 10/60s |
| `send_loyalty_sms` | `/api/1/loyalty/iiko/message/send_sms` | 20/60s |
| `send_loyalty_email` | `/api/1/loyalty/iiko/message/send_email` | 20/60s |

Особенности:
- `send_loyalty_email` — ответ `object` → обёртка возвращает `None`.
- `send_loyalty_sms` — ответ `SendSmsResponse` (sms_id для check_sms_status).
- Статусы — int-enum'ы 0..3 без имён в SDK (семантика — в docstring).

## 2. Helpers

Заготовка (решение батча).

## 3. Файловая структура

- `iikocloud/mixins/messages/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_messages_api`, 4 `ApiMethod`, 4 поля
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 4 лимита
- Тесты: `tests/unit/test_messages.py`,
  `tests/integration/messages/{__init__,test_read.py}`

## 4. Тесты

### Unit

Все 4 метода: делегирование; `None` для send_email.

### Integration

- Structure-only (`test_server`): `check_sms_sending_possibility`
  (структура: status/available_sms_count), `check_sms_status`
  (по несуществующему sms_id — валидная структура statuses).
- sends — только unit (реальные SMS/email не шлём: деньги/спам).

## 5. Definition of done

- 4 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
