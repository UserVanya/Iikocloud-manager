# Спека: модуль marketing_sources

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, лояльность-батч)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртка над единственным методом `MarketingSourcesApi` SDK.

### Метод

| Метод | Endpoint | Request → Response | Лимит |
|---|---|---|---|
| `get_marketing_sources` | `/api/1/marketing_sources` | `MarketingSourcesRequest` (organization_ids) → `MarketingSourcesResponse` | 1/60s |

Особенности: read-only справочник (iiko >= 7.2.5, `Data: dictionaries`);
`organization_ids` — список.

## 2. Helpers

Не пишем. `helpers.py` — заготовка по конвенции.

## 3. Файловая структура

- `iikocloud/mixins/marketing_sources/{__init__,core,helpers}.py`
- `iikocloud/mixins/_base.py` — lazy-геттер `get_marketing_sources_api`,
  1 `ApiMethod`, 1 поле `MethodRateLimits`
- `iikocloud/api_client_manager.py` — слот, MRO, docstring
- `iikocloud/config_reader.py` + `config.example.yml` — 1 лимит
- Тесты: `tests/unit/test_marketing_sources.py`,
  `tests/integration/dictionaries/test_marketing_sources.py`

## 4. Тесты

### Unit

Делегирование, проксирование ответа.

### Integration (read, секция `read` — данные есть на read-стенде)

- `get_marketing_sources` — correlation_id, структура; если источники
  есть — первый имеет id/name/organization_id.

## 5. Definition of done

- 1 core + helpers-заготовка, `ApiMethod`, лимит, config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
