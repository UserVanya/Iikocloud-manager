# Спека: расширение customers+ и menu+ (добор методов SDK)

Дата: 2026-07-23
Статус: утверждена (brainstorm с пользователем)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Добавить обёртки над всеми непокрытыми методами `CustomersApi` (8) и
`MenuApi` (7) установленного `iikocloud_client`. Helpers в этом модуле
не реализуются — только файлы-заготовки.

### CustomersApi (8 методов)

| Метод | Endpoint | Request | Response |
|---|---|---|---|
| `add_customer_magnet_card` | `/api/1/loyalty/iiko/customer/card/add` | `AddMagnetCardRequest` (cardNumber, cardTrack, customerId, organizationId) | `object` (пустой) |
| `remove_customer_magnet_card` | `/api/1/loyalty/iiko/customer/card/remove` | `DeleteMagnetCardRequest` (cardTrack, customerId, organizationId) | `object` |
| `add_customer_to_program` | `/api/1/loyalty/iiko/customer/program/add` | `AddCustomerToProgramRequest` (customerId?, organizationId, programId?) | `AddCustomerToProgramResponse` (userWalletId, walletId) |
| `hold_customer_balance` | `/api/1/loyalty/iiko/customer/wallet/hold` | `HoldMoneyRequest` (customerId, organizationId, walletId, sum, comment?, transactionId?) | `HoldMoneyResponse` (transactionId) |
| `cancel_customer_balance_hold` | `/api/1/loyalty/iiko/customer/wallet/cancel_hold` | `CancelHoldMoneyRequest` (organizationId, transactionId) | `object` |
| `top_up_customer_balance` | `/api/1/loyalty/iiko/customer/wallet/topup` | `ChangeUserBalanceRequest` | `object` |
| `withdraw_customer_balance` | `/api/1/loyalty/iiko/customer/wallet/chargeoff` | `ChangeUserBalanceRequest` | `object` |
| `get_loyalty_counters` | `/api/1/loyalty/iiko/get_counters` | `GetCountersRequest` (organizationId, guestIds?, metrics?, periods?) | `GetCountersResponse` (counters: GuestCounter[]) |

### MenuApi (7 методов)

| Метод | Endpoint | Request | Response |
|---|---|---|---|
| `add_products_to_stop_list` | `/api/1/stop_lists/add` | `AddProductsToStopListRequest` (organizationId, terminalGroupId, items[{productId, balance, sizeId?}]) | `CorrelationIdResponse` |
| `remove_products_from_stop_list` | `/api/1/stop_lists/remove` | `RemoveProductsFromStopListRequest` (items[{productId, sizeId?}]) | `CorrelationIdResponse` |
| `clear_stop_list` | `/api/1/stop_lists/clear` | `ClearStopListRequest` (organizationId, terminalGroupId) | `CorrelationIdResponse` |
| `check_products_in_stop_list` | `/api/1/stop_lists/check` | `CheckStopListRequest` (organizationId, terminalGroupId, items[DeliveryOrderCreateItem]) | `CheckStopListResponse` (correlationId, rejectedItems?) |
| `get_nomenclature` | `/api/1/nomenclature` | `NomenclatureRequest` (organizationId, startRevision?) | `NomenclatureResponse` (correlationId, revision, groups, products, productCategories, sizes) |
| `get_combos_info` | `/api/1/combo` | `GetCombosInfoRequest` (organizationId, extraData?) | `GetCombosInfoResponse` (comboCategories, comboSpecifications, warnings) |
| `calculate_combo_price` | `/api/1/combo/calculate` | `CalculateComboPriceRequest` (organizationId, items[DeliveryOrderCreateItem]) | `CalculateComboPriceResponse` (price, incorrectlyFilledGroups?) |

## 2. Конвенция сигнатур

Как в существующих mixin'ах: core-метод принимает SDK request-модель целиком
(`request: AddMagnetCardRequest`) и возвращает SDK response-модель.
Исключения-усиления:

- `top_up_customer_balance` / `withdraw_customer_balance`: в модели
  `ChangeUserBalanceRequest` поля `customerId`/`walletId` формально optional.
  Обёртка валидирует их наличие (ValueError до запроса) — семантически
  операция без них бессмысленна.
- `DeliveryOrderCreateItem` — полиморфная база (дискриминатор `type`):
  в тестах и примерах используем `DeliveryOrderCreateProductItem`.

Методы с «пустым» ответом (`object` в SDK): обёртка возвращает `None`.

## 3. Файловая структура

- `iikocloud/mixins/customers/core.py` — дописать 8 методов в
  `CustomersCoreMixin`.
- `iikocloud/mixins/customers/helpers.py` — уже существует с реализациями;
  не трогаем.
- `iikocloud/mixins/menu/core.py` — дописать 7 методов в `MenuCoreMixin`.
- `iikocloud/mixins/menu/helpers.py` — уже существует с реализацией
  (`get_stop_lists_by_organization`); не трогаем. Новые helpers под
  добавляемые методы в этом модуле НЕ пишем (решение пользователя) —
  оба helpers-файла остаются как есть и служат заготовками под будущие
  convenience-методы.
- `iikocloud/mixins/_base.py` — 15 новых значений в `ApiMethod`
  (locked names = snake_case имени метода SDK).
- `iikocloud/config_reader.py` — 15 новых полей в `MethodRateLimitsSettings`.
- `config.example.yml` — те же ключи.

## 4. Rate limits

| Метод | Лимит | Обоснование |
|---|---|---|
| `add/remove_customer_magnet_card`, `add_customer_to_program`, `hold/cancel/top_up/withdraw` | 100 / 60 s | как остальные customers write |
| `get_loyalty_counters` | 10 / 60 s | read-запрос |
| `add/remove_products_to_stop_list`, `clear_stop_list` | 1 / 60 s | тяжёлые редкие мутации, рекомендация интеграторов по stop_lists |
| `check_products_in_stop_list` | 10 / 60 s | read-проверка |
| `get_nomenclature` | 1 / 60 s | правило iiko: минута между порциями, ≤5 орг/запрос |
| `get_combos_info`, `calculate_combo_price` | 10 / 60 s | read/расчёт |

## 5. Тесты

### Unit (моки SDK, паттерн `tests/unit/test_customers.py` / `test_menu.py`)

Все 15 методов: корректный вызов SDK с переданной request-моделью,
проксирование ответа, `None` для `object`-ответов, валидация
`customerId`/`walletId` в top_up/withdraw (ValueError без вызова SDK).

### Integration real API (`IIKOCLOUD_TEST_CONFIG=config.test.yml`)

Read (секция `read`):
- `get_nomenclature` (startRevision=0; ответ содержит revision, списки)
- `get_combos_info`
- `get_loyalty_counters` (по известному guest из конфига, если есть —
  иначе пропуск с причиной; см. открытые точки)
- `check_products_in_stop_list` (item через `DeliveryOrderCreateProductItem`)

Write (`danger_write`, секция `write`):
- карты: `add_customer_magnet_card` → `remove_customer_magnet_card`
  (на тестовом клиенте из lifecycle)
- программа: `add_customer_to_program` (если в write-организации есть
  программа лояльности — иначе skip с причиной)
- баланс, цикл A: `hold_customer_balance` → `cancel_customer_balance_hold`
- баланс, цикл B: `top_up_customer_balance` → `withdraw_customer_balance`
  (одинаковая sum; при падении между ними — отдельный тест-напоминание
  в отчёте)
- стоп-листы: `add_products_to_stop_list` → `check_products_in_stop_list`
  (продукт в rejectedItems) → `remove_products_from_stop_list` →
  `clear_stop_list`. Асинхронные мутации: после correlationId ждём
  поллингом применения через повторный `check`/`get_stop_lists`
  (без обёртки OperationsApi — поллинг в тестовом коде).

## 6. Открытые точки (решаются при реализации)

- `get_loyalty_counters`: семантика значений enum'ов `CounterMetric` (0..3)
  и `CounterPeriod` (0..12) в SDK не описана — сверить с документацией iiko
  и зафиксировать в docstring.
- Наличие программы лояльности / wallet на write-организации — проверить
  при первом прогоне; при отсутствии тесты skip с явной причиной.
- Данные для read-теста counters (guest id) — взять из конфига или создать
  клиента в рамках теста.

## 7. Definition of done

- 15 методов в core, `ApiMethod`, rate limits, config.example.yml.
- Unit-тесты зелёные (включая существующие 77).
- Integration: read и `danger_write` прогнаны вживую против
  `config.test.yml`, зелёные.
- mypy/ruff чистые по изменённым файлам.
