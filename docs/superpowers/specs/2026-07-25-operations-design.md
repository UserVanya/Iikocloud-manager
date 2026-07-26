# Спека: модуль operations

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч «прочее»)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртка над единственным методом `OperationsApi` SDK + helper polling'а.

### Метод и лимит

| Метод | Endpoint | Лимит |
|---|---|---|
| `get_command_status` | `/api/1/commands/status` | 60/60s |

Особенности:
- Read-only; лимит 60/60s — это polling-метод (интервал 2с = 30/мин
  на команду), выбран с запасом.
- Ответ — полиморф по `state`: `SuccessCommandStatus` /
  `InProgressCommandStatus` / `ErrorCommandStatus` (с `error_reason`).
- HTTP 410 — correlationId устарел, прекращать polling.

## 2. Helpers (решение батча — делаем)

- `wait_command(correlation_id: str | UUID, organization_id: str | UUID, *,
  timeout: float = 30.0, interval: float = 2.0)
  -> SuccessCommandStatus | ErrorCommandStatus` — polling
  `get_command_status` до терминального состояния:
  - `Success` → возврат статуса;
  - `Error` → возврат статуса (вызывающий разбирает error_reason);
  - HTTP 410 → `IikoCloudApiException` (correlationId устарел);
  - timeout → `TimeoutError` с последним состоянием в сообщении.
  Interval фиксируется 2.0s (лимит метода 60/60s).

## 3. Файловая структура

- `iikocloud/mixins/operations/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_operations_api`, 1 `ApiMethod`, 1 поле
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 1 лимит
- Тесты: `tests/unit/test_operations.py`,
  `tests/integration/operations/{__init__,test_status.py}`

## 4. Тесты

### Unit

Делегирование; `wait_command`: Success сразу, InProgress→Success,
Error-статус, timeout → TimeoutError (моки с side_effect-последовательностями,
monkeypatch asyncio.sleep или малые interval).

### Integration danger_write

- `get_command_status` по correlation_id реальной команды: мутация
  стоп-листа (add) → сразу status (InProgress/Success — валидный ответ).
- `wait_command` по той же команде → терминальный статус Success
  (или Error с разбором, если стенд отклонил; фиксируем в отчёте).
  Cleanup: remove + clear стоп-листа (как в test_stop_lists_write).

## 5. Definition of done

- 1 core + wait_command, `ApiMethod`, лимит, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
