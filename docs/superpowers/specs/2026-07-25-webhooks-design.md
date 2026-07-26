# Спека: модуль webhooks

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч «прочее»)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над обоими методами `WebhooksApi` SDK (deprecated нет).

### Методы и лимиты

| Метод | Endpoint | Лимит |
|---|---|---|
| `get_webhook_settings` | `/api/1/webhooks/settings` | 1/60s |
| `update_webhook_settings` | `/api/1/webhooks/update_settings` | 1/60s |

Особенности:
- `get_webhook_settings` — ответ содержит чувствительный `auth_token`
  (не логировать значение в тестах/отчётах).
- `update_webhook_settings` — перезаписывает webhook-конфиг api-логина
  (`web_hooks_uri` обязателен, фильтры optional-nullable).
- `WebHooksFilter` — вложенные фильтры по типам событий (deliveryOrder,
  tableOrder, reserve, stopList, personalShift, nomenclature,
  businessHoursAndMapping).

## 2. Helpers

Заготовка (решение батча).

## 3. Файловая структура

- `iikocloud/mixins/webhooks/{__init__,core,helpers}.py`
- `_base.py` — lazy-геттер `get_webhooks_api`, 2 `ApiMethod`, 2 поля
- `api_client_manager.py` — слот, MRO, docstring
- `config_reader.py` + `config.example.yml` — 2 лимита
- Тесты: `tests/unit/test_webhooks.py`,
  `tests/integration/webhooks/{__init__,test_settings.py}`

## 4. Тесты

### Unit

Оба метода: делегирование, проксирование ответа.

### Integration danger_write (с восстановлением)

1. `get_webhook_settings` — сохранить исходные (uri, auth_token, filter).
2. `update_webhook_settings` — тестовый URI
   (`https://example.com/iikocloud-manager-test-hook`, auth_token=None).
3. Повторный `get_webhook_settings` — URI совпадает с тестовым
   (проверка применения).
4. finally: `update_webhook_settings` обратно на исходные значения
   (uri/auth_token/filter из шага 1); auth_token не выводить в логи.

## 5. Definition of done

- 2 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
