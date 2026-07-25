# Спека: модуль delivery_restrictions

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч restrictions+drafts+addresses)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 2 методами `DeliveryRestrictionsApi` SDK (deprecated-методов
нет; deprecated только поле `organization_id` внутри
`GetAllowedRestrictionsRequest` — используем `organization_ids`).

### Методы

| Метод | Endpoint | Request → Response | Лимит |
|---|---|---|---|
| `get_allowed_delivery_restrictions` | `/api/1/delivery_restrictions/allowed` | `GetAllowedRestrictionsRequest` → `GetAllowedRestrictionsResponse` | 20/60s |
| `get_delivery_restrictions` | `/api/1/delivery_restrictions` | `GetDeliveryRestrictionsRequest` → `GetDeliveryRestrictionsResponse` | 1/60s |

Особенности:
- Оба read-only (restriction groups: `Orders: preparing`, `Data: dictionaries`).
- `get_allowed_delivery_restrictions`: единственное обязательное поле —
  `is_courier_delivery`; `organization_ids` (не deprecated-вариант).
  Ответ: `is_allowed`, `allowed_items` (терминальные группы + длительность),
  `rejected_items` (коды причин: SumIsLessThenMinimum, OutOfTerminalZone...).
- `get_delivery_restrictions`: единственное поле — `organization_ids` (список).
  Ответ — тяжёлый справочник зон/ограничений (~25 полей на организацию).

## 2. Helpers

Не пишем (решение батча). `helpers.py` — заготовка по конвенции
(`DeliveryRestrictionsHelpersMixin` наследует core, без новых методов).

## 3. Файловая структура

- `iikocloud/mixins/delivery_restrictions/{__init__,core,helpers}.py`
- `iikocloud/mixins/_base.py` — lazy-геттер `get_delivery_restrictions_api`,
  2 `ApiMethod`, 2 поля `MethodRateLimits`
- `iikocloud/api_client_manager.py` — слот, MRO, docstring
- `iikocloud/config_reader.py` + `config.example.yml` — 2 лимита
- Тесты: `tests/unit/test_delivery_restrictions.py`,
  `tests/integration/delivery_restrictions/test_read.py`

## 4. Тесты

### Unit

Оба core-метода: делегирование, проксирование ответа.

### Integration (structure-only, маркер `test_server`)

- `get_delivery_restrictions` — вызов, correlation_id, структура.
- `get_allowed_delivery_restrictions` — `is_courier_delivery=True` +
  `organization_ids`; проверка `is_allowed`/структуры allowed/rejected
  (без адреса сервер может вернуть rejected — это валидный ответ,
  проверяем структуру, не бизнес-результат).

## 5. Definition of done

- 2 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
