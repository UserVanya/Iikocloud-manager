# Спека: модуль customer_categories

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, лояльность-батч)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 3 методами `CustomerCategoriesApi` SDK (deprecated нет).

### Методы

| Метод | Endpoint | Request → Response | Лимит |
|---|---|---|---|
| `get_customer_categories` | `/api/1/loyalty/iiko/customer_category` | `GetCategoriesRequest` → `GetCategoriesResponse` | 1/60s |
| `add_customer_category` | `/api/1/loyalty/iiko/customer_category/add` | `ChangeCategoryForCustomerRequest` → `None` (object) | 100/60s |
| `remove_customer_category` | `/api/1/loyalty/iiko/customer_category/remove` | `ChangeCategoryForCustomerRequest` → `None` (object) | 100/60s |

Особенности:
- add/remove разделяют request-модель (kwarg `change_category_for_customer_request`)
  и возвращают нетипизированный `object` → обёртки возвращают `None`.
- `organization_id` везде одиночный.

## 2. Helpers

Не пишем. `helpers.py` — заготовка по конвенции.

## 3. Файловая структура

- `iikocloud/mixins/customer_categories/{__init__,core,helpers}.py`
- `iikocloud/mixins/_base.py` — lazy-геттер `get_customer_categories_api`,
  3 `ApiMethod`, 3 поля `MethodRateLimits`
- `iikocloud/api_client_manager.py` — слот, MRO, docstring
- `iikocloud/config_reader.py` + `config.example.yml` — 3 лимита
- Тесты: `tests/unit/test_customer_categories.py`,
  `tests/integration/customers/test_categories.py`

## 4. Тесты

### Unit

Все 3 метода: делегирование, `None` для add/remove, общий kwarg у обеих мутаций.

### Integration

- Structure-only (`test_server`, write-секция): `get_customer_categories` —
  структура + если категории есть, первая валидна.
- danger_write (write-секция): add → remove на свежесозданном тестовом
  клиенте (фикстура test_customer-паттерн из loyalty_write); category_id —
  первая активная из `get_customer_categories` write-стенда (skip, если
  категорий нет). Cleanup: remove в finally + удаление клиента.

## 5. Definition of done

- 3 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
