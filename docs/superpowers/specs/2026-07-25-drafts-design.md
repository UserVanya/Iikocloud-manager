# Спека: модуль drafts

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч restrictions+drafts+addresses)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 8 методами `DraftsApi` SDK (deprecated-методов нет).

### Методы

| Метод | Endpoint | Request → Response | Лимит |
|---|---|---|---|
| `create_delivery_draft` | `/api/1/deliveries/drafts/create` | `CreateDraftRequest` → `CreateOrSaveDraftResponse` | 100/60s |
| `save_delivery_draft` | `/api/1/deliveries/drafts/save` | `SaveDraftRequest` → `CreateOrSaveDraftResponse` | 100/60s |
| `commit_delivery_draft` | `/api/1/deliveries/drafts/commit` | `CommitDraftRequest` → `OrderResponse` | 20/60s |
| `delete_delivery_draft` | `/api/1/deliveries/drafts/delete` | `DeleteDraftRequest` → `CorrelationIdResponse` | 100/60s |
| `lock_delivery_draft` | `/api/1/deliveries/drafts/lock` | `LockOrUnlockDraftRequest` → `CorrelationIdResponse` | 100/60s |
| `unlock_delivery_draft` | `/api/1/deliveries/drafts/unlock` | `LockOrUnlockDraftRequest` → `CorrelationIdResponse` | 100/60s |
| `get_delivery_draft_by_id` | `/api/1/deliveries/drafts/by_id` | `GetDraftRequest` → `GetDraftResponse` | 20/60s |
| `get_delivery_drafts_by_filter` | `/api/1/deliveries/drafts/by_filter` | `FilterDraftsRequest` → `FilterDraftsResponse` | 20/60s |

Особенности:
- `commit` финализирует черновик в реальный заказ во Front (≈ создание
  заказа — лимит как у create_delivery_order).
- `DeliveryOrderDraft` обязательные поля: `menu_id: str`, `phone: str`,
  `items`. `save` требует `employee_id` и `order.id` целевого черновика.
- `by_filter` — первая настоящая пагинация в SDK (`offset`/`limit`).
- `lock`/`unlock` требуют `employee_id`.

## 2. Helpers

Не пишем (решение батча). Позиции черновика собираются существующими
`build_product_item`/`build_compound_item`. `helpers.py` — заготовка.

## 3. Файловая структура

- `iikocloud/mixins/drafts/{__init__,core,helpers}.py`
- `iikocloud/mixins/_base.py` — lazy-геттер `get_drafts_api`,
  8 `ApiMethod`, 8 полей `MethodRateLimits`
- `iikocloud/api_client_manager.py` — слот, MRO, docstring
- `iikocloud/config_reader.py` + `config.example.yml` — 8 лимитов
- Тесты: `tests/unit/test_drafts.py`,
  `tests/integration/drafts/test_write.py`

## 4. Тесты

### Unit

Все 8 core-методов: делегирование, проксирование ответа.

### Integration danger_write (секция `write`)

Lifecycle БЕЗ commit (решение пользователя — commit только unit):

1. Гард на живой фронт (как в deliveries) — иначе skip.
2. `create_delivery_draft`: `menu_id` — из внешних меню стенда
   (`get_external_menus`, fallback — значение из конфига/skip),
   тестовый телефон, один продукт через `build_product_item`.
3. `get_delivery_draft_by_id` — черновик читается, id совпадает.
4. `save_delivery_draft` — обновление (тот же `order.id`,
   `employee_id` — из конфига стенда или skip, если не задан;
   открытая точка — откуда брать employee).
5. `get_delivery_drafts_by_filter` — черновик находится по phone.
6. Cleanup: `delete_delivery_draft` в `finally`.

## 5. Открытые точки (решаются при реализации)

- Источник `menu_id` на стенде (external menus могут отсутствовать —
  тогда ключ `menu_id` в write-секции config.test.yml, как program_id).
- Источник `employee_id` для save/lock (аналогично — ключ конфига).
- lock/unlock в real-цикл не включаем (нужен employee_id + состояние);
  при наличии employee_id в конфиге — добавить опционально.

## 6. Definition of done

- 8 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit зелёные, ruff+mypy чистые.
- Integration danger_write прогнан живьём (или skip с причиной).
