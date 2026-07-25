# Спека: модуль discounts_and_promotions

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем, лояльность-батч)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над всеми 6 методами `DiscountsAndPromotionsApi` SDK (все read-only,
deprecated-методов нет; obsolete — только поля верхнего уровня
`CalculateCheckinRequest`, их не используем).

### Методы

| Метод | Endpoint | Request → Response | Лимит |
|---|---|---|---|
| `calculate_loyalty_checkin` | `/api/1/loyalty/iiko/calculate` | `CalculateCheckinRequest` → `CalculateCheckinResponse` | **1000/60s** |
| `get_coupon_info` | `/api/1/loyalty/iiko/coupons/info` | `CouponInfoRequest` → `CouponInfoResponse` | 10/60s |
| `get_coupon_series` | `/api/1/loyalty/iiko/coupons/series` | `SeriesWithNotActivatedCouponsRequest` → `SeriesWithNotActivatedCouponsResponse` | 1/60s |
| `get_loyalty_manual_conditions` | `/api/1/loyalty/iiko/manual_condition` | `GetByOrganizationIdRequest` → `GetManualConditionsResponse` | 1/60s |
| `get_loyalty_programs` | `/api/1/loyalty/iiko/program` | `GetProgramsRequest` → `GetProgramsResponse` | 1/60s |
| `get_non_activated_coupons_by_series` | `/api/1/loyalty/iiko/coupons/by_series` | `NotActivatedCouponRequest` → `NotActivatedCouponResponse` | 10/60s |

Особенности:
- `calculate_loyalty_checkin` — расчёт на каждый превью заказа в боевых
  интеграциях, поэтому высокий лимит (решение пользователя).
- `GetByOrganizationIdRequest.organization_id` необязателен в SDK —
  в обёртке валидируем наличие (ValueError до вызова SDK).
- `calculate`: верхнеуровневые `coupon`/`applicable_manual_conditions`/
  `dynamic_discounts` в request — obsolete; используем `order.loyalty_info`.

## 2. Helpers (решение пользователя — делаем)

- `calculate_order_loyalty(organization_id, items, phone, *, coupon=None,
  customer=None, applicable_manual_conditions=None, order_service_type=None,
  terminal_group_id=None) -> CalculateCheckinResponse` — короткая форма
  `calculate_loyalty_checkin`: собирает `DeliveryOrderCreatePayload`
  (phone, items, loyalty_info из coupon/conditions, customer) +
  `CalculateCheckinRequest`. items — через существующие
  `build_product_item`/`build_compound_item`.

## 3. Файловая структура

- `iikocloud/mixins/discounts/{__init__,core,helpers}.py`
- `iikocloud/mixins/_base.py` — lazy-геттер `get_discounts_and_promotions_api`,
  6 `ApiMethod`, 6 полей `MethodRateLimits`
- `iikocloud/api_client_manager.py` — слот, MRO, docstring
- `iikocloud/config_reader.py` + `config.example.yml` — 6 лимитов
- Тесты: `tests/unit/test_discounts.py`,
  `tests/integration/customers/test_discounts_read.py`

## 4. Тесты

### Unit

Все 6 core-методов: делегирование, проксирование; валидация
`organization_id` для manual_conditions (ValueError без вызова SDK).
Helper: сборка payload (loyalty_info с coupon/conditions, customer
прокидывается, service_type).

### Integration (structure-only, маркер `test_server`, write-секция)

- `get_loyalty_programs` — программа «Бонусы» существует (структура +
  непустой список, id программы валиден).
- `get_loyalty_manual_conditions`, `get_coupon_series` — структура.
- `get_coupon_info` — по номеру из `get_non_activated_coupons_by_series`
  (skip, если серий/купонов нет).
- `calculate_loyalty_checkin` — через helper `calculate_order_loyalty`
  с реальным продуктом (фикстура product), минимальный заказ;
  проверка структуры ответа (loyalty_program_results/warnings — списки).

## 5. Definition of done

- 6 core + 1 helper, `ApiMethod`, лимиты (calculate — 1000/60s),
  config.example.yml, MRO.
- Unit + integration зелёные, ruff+mypy чистые.
