# Мастер-спека: полное покрытие iikocloud SDK

Дата: 2026-07-23
Статус: утверждена (brainstorm с пользователем)

## 1. Цель и scope

Покрыть mixin'ами все публичные API-классы установленного `iikocloud_client`,
кроме `DeprecatedApi`. На момент аудита (2026-07-23) не покрыто 33 класса;
в scope входят 32 из них (`DeprecatedApi` исключён), плюс неиспользуемые
методы внутри уже покрытых классов.

Уже покрыто (MVP, не входит в эту спеку): `AuthorizationApi` (v2),
`OrganizationsApi`, `TerminalGroupsApi` (частично), `CustomersApi` (частично),
`MenuApi` (частично), `DictionariesApi`.

### Непокрытые классы (33)

- Deliveries/Orders (6): `DeliveriesCreateAndUpdateApi`, `DeliveriesRetrieveApi`,
  `DeliveryRestrictionsApi`, `DraftsApi`, `OrdersApi`, `AddressesApi`
- Лояльность/клиенты (3): `CustomerCategoriesApi`, `DiscountsAndPromotionsApi`,
  `MarketingSourcesApi`
- Прочее (7): `EmployeesApi`, `MessagesApi`, `NotificationsApi`, `OperationsApi`,
  `ReportApi`, `WebhooksApi`, `BanquetsReservesApi`
- Invoice Processing (16): `PublicApiInvoiceProcessingAccountTransactionsApi`,
  `...CounteragentsApi`, `...DisassembleDocumentApi`, `...DocumentTransactionsApi`,
  `...IncomingInvoicesApi`, `...IncomingReturnedInvoiceApi`,
  `...IncomingServiceApi`, `...InternalTransferApi`, `...NomenclatureApi`,
  `...OutgoingInvoicesApi`, `...OutgoingServiceApi`, `...ProductionDocumentApi`,
  `...ReturnedInvoiceApi`, `...SalesDocumentApi`, `...TransformationDocumentApi`,
  `...WriteoffDocumentApi`

### Добор методов в покрытых классах (отдельные модули-расширения)

- `CustomersApi`: `add_customer_magnet_card`, `add_customer_to_program`,
  `hold/cancel/top_up/withdraw_customer_balance`, `get_loyalty_counters`,
  `remove_customer_magnet_card` и др. неиспользуемые
- `MenuApi`: stop-list мутации, `get_nomenclature`, `get_combos_info`,
  `calculate_combo_price` и др.
- `TerminalGroupsApi`: `awake_terminal_groups`

## 2. Гранулярность: один модуль = один API-класс SDK

Каждый класс — отдельный модуль с собственным циклом
«обсуждение → спека → план → реализация». Доборы методов — модули-расширения
существующих доменов (`customers+`, `menu+`, `terminal_groups+`).

## 3. Структура модуля (конвенция)

- `iikocloud/mixins/<domain>/core.py` — тонкие async-обёртки над методами SDK
  через `execute_with_retry` (rate limit + retry при 401), как в существующих
  доменах.
- `iikocloud/mixins/<domain>/helpers.py` — удобные составные методы.
  Наполнение предлагается агентом в brainstorm модуля, утверждается
  пользователем.
- Регистрация mixin'а в `IikoCloudApiClientManager`.
- Rate limits: новые поля в `MethodRateLimitsSettings`
  (`iikocloud/config_reader.py`), значения по схеме из раздела 5.
- Обновление `config.example.yml` новыми ключами rate limits.

## 4. Порядок реализации (ценностный)

1. Deliveries-блок: `deliveries_create_and_update`, `deliveries_retrieve`,
   `delivery_restrictions`, `drafts`, `orders`, `addresses`
2. Лояльность и добор: `customer_categories`, `discounts_and_promotions`,
   `marketing_sources`, `customers+`, `menu+`, `terminal_groups+`
3. Прочее: `employees`, `messages`, `notifications`, `operations`, `report`,
   `webhooks`, `banquets_reserves`
4. Invoice Processing: 16 классов (порядок внутри блока определяется
   при старте блока)

Порядок может корректироваться пользователем перед стартом очередного модуля.

## 5. Rate limiting (схема A')

Официальной таблицы per-method лимитов iiko Cloud в открытом доступе нет
(проверено: SDK не содержит данных, swagger-портал недоступен анонимно).
Поэтому:

- Консервативные дефолты по классу операции:
  - read-справочники: 1 req / 60 s
  - read-запросы: 10 req / 60 s
  - write-операции: 100 req / 60 s (как текущие customers)
  - auth: 1 req / 5 s (уже есть)
- Зафиксированные известные правила iiko:
  - номенклатура: не более 5 организаций за запрос от одного API-логина,
    следующая порция — через минуту; параллельные запросы номенклатуры v1
    запрещены транспортом; без `revision` действует отдельное жёсткое окно
    (ошибка «Too many requests without revision...»)
  - stop_lists: рекомендация интеграторов — не чаще 1 раза в 5 минут
- Точечная корректировка при получении 429 в real API-тестах.
- Все значения переопределяемы через `config.yml` (как сейчас).

Источники: ru.iiko.help (Changelog iikoCloud API, «Работа с номенклатурой»,
«Ограничения и рекомендации»), apimenu.ru FAQ.

## 6. Тестирование

- Unit (моки SDK) — обязательно для каждого модуля, паттерн как в
  `tests/unit/`.
- Integration real API (`tests/integration/<domain>/`):
  - read — всегда, где применимо, на секции `read` из `config.test.yml`
    (путь через `IIKOCLOUD_TEST_CONFIG`).
  - write — с маркером `danger_write`, только на выделенной write-организации
    из секции `write`, паттерн create → cancel/cleanup. Включены при прогоне
    с заданным `IIKOCLOUD_TEST_CONFIG`.
  - Модули без доступного контура (например, `webhooks` — нужен
    callback-приёмник) помечаются в спеке модуля как «unit-only»
    с обоснованием.

## 7. Процесс на каждый модуль

1. Агент штудирует методы класса в установленном SDK и приносит на обсуждение:
   - список методов с сигнатурами и моделями запросов/ответов;
   - какие параметры принимать (простые типы vs модели SDK);
   - предлагаемые helpers;
   - что тестируем вживую (read/write/unit-only);
   - предлагаемые rate limits.
2. После утверждения — спека `docs/superpowers/specs/YYYY-MM-DD-<module>-design.md`.
3. План реализации (superpowers writing-plans).
4. Реализация, прогон unit + integration, коммит.

## 8. Открытые точки (решаются в brainstorm соответствующего модуля)

- Invoice Processing: тот ли токен/base URL, что у основного Cloud API.
- Webhooks: контур тестирования (нужен приёмник callback'ов).
- Доступность write-операций заказов (create/confirm/cancel delivery)
  на выделенной write-организации.
