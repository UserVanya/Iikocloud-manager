# Спека: модуль employees

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч «прочее»)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 10 методами `EmployeesApi` SDK (deprecated нет).

### Методы и лимиты

| Метод | Endpoint | Лимит |
|---|---|---|
| `get_couriers` | `/api/1/employees/couriers` | 1/60s |
| `get_couriers_by_role` | `/api/1/employees/couriers/by_role` | 1/60s |
| `get_employee_info` | `/api/1/employees/info` | 1/60s |
| `get_active_courier_locations` | `/api/1/employees/couriers/active_location` | 10/60s |
| `get_active_courier_locations_by_terminal` | `/api/1/employees/couriers/active_location/by_terminal` | 10/60s |
| `get_courier_location_history` | `/api/1/employees/couriers/locations/by_time_offset` | 10/60s |
| `get_personal_session_info` | `/api/1/employees/shift/is_open` | 10/60s |
| `get_terminal_groups_of_employee` | `/api/1/employees/shifts/by_courier` | 10/60s |
| `open_personal_session` | `/api/1/employees/shift/clockin` | 100/60s |
| `close_personal_session` | `/api/1/employees/shift/clockout` | 100/60s |

Особенности:
- open/close — команды (статус через commands/status); ответ
  `ChangePersonalSessionResponse` (correlation_id + error).
- `get_terminal_groups_of_employee` — без organizationId в request.
- RMS-обёртки ответов: `{organization_id, items}`.

## 2. Helpers

Заготовка (решение батча).

## 3. Файловая структура

- `iikocloud/mixins/employees/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_employees_api`, 10 `ApiMethod`, 10 полей
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 10 лимитов
- Тесты: `tests/unit/test_employees.py`,
  `tests/integration/employees/{__init__,test_read.py,test_shifts.py}`

## 4. Тесты

### Unit

Все 10 методов: делегирование, проксирование ответа.

### Integration

- Structure-only (`test_server`): get_couriers, get_employee_info
  (по TestUser из get_couriers), get_active_courier_locations,
  get_courier_location_history, get_terminal_groups_of_employee.
- danger_write (смены, TestUser из конфига `employee_id`):
  `get_personal_session_info` (фиксация исходного состояния) →
  `open_personal_session` → info (opened=True) → `close_personal_session`
  в finally (возврат к исходному состоянию; если сессия была открыта до
  теста — не трогаем, skip).

## 5. Definition of done

- 10 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
