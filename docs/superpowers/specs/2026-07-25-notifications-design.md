# Спека: модуль notifications

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч «прочее»)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртка над единственным методом `NotificationsApi` SDK.

### Метод и лимит

| Метод | Endpoint | Лимит |
|---|---|---|
| `send_notification` | `/api/1/notifications/send` | 100/60s |

Особенности:
- Request — полиморф `SendNotificationRequest` (дискриминатор `messageType`);
  единственный подкласс — `OrderAttentionNotificationRequest`
  (`message_type="order_attention"` явно; + `order_id`, `order_source`,
  `additional_info`).
- Ответ `CorrelationIdResponse`.

## 2. Helpers

Заготовка (решение батча).

## 3. Файловая структура

- `iikocloud/mixins/notifications/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_notifications_api`, 1 `ApiMethod`, 1 поле
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 1 лимит
- Тесты: `tests/unit/test_notifications.py`,
  `tests/integration/notifications/{__init__,test_write.py}`

## 4. Тесты

### Unit

Делегирование с `OrderAttentionNotificationRequest`.

### Integration danger_write

Создать заказ (паттерн deliveries: реальный продукт, `DeliveryByClient`,
гард на живой фронт) → `send_notification` (order_attention на id заказа;
проверка `correlation_id`) → cancel заказа в finally.

## 5. Definition of done

- 1 core + helpers-заготовка, `ApiMethod`, лимит, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
