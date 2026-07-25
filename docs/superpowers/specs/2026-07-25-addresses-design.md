# Спека: модуль addresses

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, батч restrictions+drafts+addresses)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 4 методами `AddressesApi` SDK (deprecated-методов нет,
все read-only, restriction group `Data: geo`).

### Методы

| Метод | Endpoint | Request → Response | Лимит |
|---|---|---|---|
| `get_cities` | `/api/1/cities` | `CitiesRequest` (organization_ids, include_deleted?) → `CitiesResponse` | 1/60s |
| `get_regions` | `/api/1/regions` | `RegionsRequest` (organization_ids) → `RegionsResponse` | 1/60s |
| `get_streets_by_city` | `/api/1/streets/by_city` | `StreetsByCityRequest` (organization_id, city_id, include_deleted?) → `StreetsResponse` | 1/60s |
| `get_streets_by_id` | `/api/1/streets/by_id` | `StreetsByIdRequest` (organization_id, ids?, classifier_ids?) → `StreetsByIdResponse` | 1/60s |

Особенности:
- `get_cities`/`get_regions` — список организаций, ответ сгруппирован
  per-organization (`items` + `organization_id`).
- `get_streets_*` — одиночная организация, плоский список.
- `get_streets_by_id`: ids XOR classifier_ids не валидируется в SDK
  (серверная валидация). Клиентскую валидацию НЕ добавляем — сервер
  допускает оба/ни одного по своим правилам, не навязываем свои.
- `StreetsByIdResponse.correlation_id` — Optional (единственный такой).

## 2. Helpers

Не пишем (решение батча). `helpers.py` — заготовка по конвенции.

## 3. Файловая структура

- `iikocloud/mixins/addresses/{__init__,core,helpers}.py`
- `iikocloud/mixins/_base.py` — lazy-геттер `get_addresses_api`,
  4 `ApiMethod`, 4 поля `MethodRateLimits`
- `iikocloud/api_client_manager.py` — слот, MRO, docstring
- `iikocloud/config_reader.py` + `config.example.yml` — 4 лимита
- Тесты: `tests/unit/test_addresses.py`,
  `tests/integration/addresses/test_read.py`

## 4. Тесты

### Unit

Все 4 core-метода: делегирование, проксирование ответа.

### Integration (read, секция `read` — обычный read-контур)

- `get_cities` — correlation_id, структура; если города есть — первый
  `id`/`name` валидны.
- `get_regions` — структура.
- `get_streets_by_city` — city_id из `get_cities` той же организации
  (skip, если городов нет).
- `get_streets_by_id` — ids из `get_streets_by_city` (skip, если улиц нет);
  проверка, что вернувшиеся улицы имеют id/city_id/city_name/street_name.

## 5. Definition of done

- 4 core + helpers-заготовка, `ApiMethod`, лимиты, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
