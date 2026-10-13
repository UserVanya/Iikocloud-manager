# Iikocloud-manager

Асинхронный клиент для iikocloud API с rate limiting и автоматическим управлением токенами.

## Установка

Требуется Python ≥ 3.12 и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/UserVanya/Iikocloud-manager.git
cd Iikocloud-manager
uv sync
```

Зависимость `iikocloud-client` подтягивается из git (см. `pyproject.toml`).

## Конфигурация (auth v2)

Скопируйте шаблон и заполните учётные данные:

```bash
cp config.example.yml config.yml
cp .env.example .env
```

Файл `config.yml` (путь задаётся через `IIKOCLOUD_CONFIG` в `.env`):

```yaml
iikocloud:
  api_key: "your_api_key"
  app_id: "your_app_id"
  client_secret: "your_client_secret"
  rate_limits:
    auth:
      max_requests: 1
      time_window_seconds: 5.0
    get_organizations:
      max_requests: 1
      time_window_seconds: 10.0
    # ... остальные методы — см. config.example.yml
```

Используется только auth v2 (`api_key` + `app_id` + `client_secret`). Legacy `api_login` не поддерживается.

## Быстрый старт

```python
import asyncio

from iikocloud import IikoCloudApiClientManager, get_iikocloud_config


async def main() -> None:
    config = get_iikocloud_config()
    manager = await IikoCloudApiClientManager.from_config(config)
    try:
        orgs = await manager.get_organizations()
        print(len(orgs.organizations))
    finally:
        await IikoCloudApiClientManager.close_all()


asyncio.run(main())
```

Или запустите демо:

```bash
uv run python main.py
```

### Правило `close_all()`

Менеджер — Multitone (один экземпляр на набор credentials). Между циклами `asyncio.run()` или при завершении приложения **обязательно** вызывайте `await IikoCloudApiClientManager.close_all()` — это закрывает HTTP-клиенты, сбрасывает TokenManager и глобальный rate limiter.

### Окна чтения меню (0.3.0)

Меню нового адреса (`get_external_menu_v3_by_id`) читается через окна, а не через ожидающий
лимитер метода: у ключа — общее окно (по умолчанию одно меню в 30 с), у каждой организации
ключа — своё (одно меню в 120 с; несколько меню одной организации делят его окно). Менеджер
**не ждёт** окна: не пора — сразу `MenuTooEarly` с числом секунд (`seconds`) и причиной
(`reason`: `key`, `organization` или `paused`). Ответ iiko «слишком часто» (429) на чтение меню
ставит на паузу чтение меню всего ключа (по умолчанию 5 минут); исключение iiko при этом
пробрасывается как было.

Окна задаются в конфиге (`menu_windows`, см. `config.example.yml`) и правятся на ходу —
`manager.set_menu_limits(per_key_sec=…, per_organization_sec=…, pause_after_429_sec=…)`;
`manager.menu_state()` отдаёт окна и остаток паузы для экрана состояния. Предел метода
`get_external_menu_v3_by_id` в `rate_limits` больше не действует: его заменяет страховка по окну
ключа.

**Смена поведения с 0.2.x:** вызывающий `get_external_menu_v3_by_id` раньше ждал окна до двух
минут, теперь получает `MenuTooEarly` — ловите его и повторяйте через `seconds`.

### Меню вместе с ответом iiko (0.4.0)

Рядом с `get_external_menu_v3_by_id` — `get_external_menu_v3_by_id_with_answer(request)`: то же
чтение меню, но кроме разобранного `MenuV3` отдаётся и тело ответа iiko как есть — например,
чтобы показать сотруднику, что именно прислал iiko. Возвращает `MenuV3Answer`:

- `menu` — меню `MenuV3`, разобранное так же, как в `get_external_menu_v3_by_id`;
- `raw` — тело ответа байт в байт (те же пробелы, порядок полей и кириллица; сжатие передачи
  вроде gzip снимает HTTP-клиент);
- `content_type` — заголовок Content-Type ответа (`None`, если iiko его не прислал).

Один запрос в iiko на попытку: меню разбирается из тех же байт. Окна ключа и организации,
страховка метода по окну ключа, повтор после 401 и пауза после 429 — общие с
`get_external_menu_v3_by_id`: прочитали меню одним методом — другой для той же организации
ответит `MenuTooEarly`. Ошибки iiko (401, 429, 5xx) пробрасываются теми же исключениями SDK.
Если iiko ответил успехом, но тело в `MenuV3` не разбирается, — `MenuAnswerUnreadable`: тело
в `raw`, Content-Type в `content_type`, причина (обычно `ValidationError`) — в `__cause__`.

```python
from iikocloud import MenuAnswerUnreadable, MenuTooEarly

try:
    answer = await manager.get_external_menu_v3_by_id_with_answer(request)
except MenuTooEarly as early:
    ...  # повторить через early.seconds
except MenuAnswerUnreadable as unreadable:
    ...  # показать unreadable.raw — что прислал iiko
else:
    menu, raw = answer.menu, answer.raw
```

### Сотрудники (0.5.0)

Раздел сотрудников собран из трёх частей; все методы — с теми же пределами (свой предел на
метод + общий), повтором после 401 и исключениями SDK, что и прочие разделы. Пределы — в
`rate_limits` (см. `config.example.yml`).

| Что | Метод менеджера | Адрес iiko | Предел |
|---|---|---|---|
| Курьеры организации | `get_couriers`, помощник `list_organization_couriers(org_id)` | `/api/1/employees/couriers` | 1/мин |
| Курьеры с проверкой роли | `get_couriers_by_role` | `/api/1/employees/couriers/by_role` | 1/мин |
| Карточка по id (телефон, cellPhone) | `get_employee_info` | `/api/1/employees/info` | 1/мин |
| Открыть / закрыть личную смену | `open_personal_session`, `close_personal_session` | `/api/1/employees/shift/clockin`, `clockout` | 100/мин |
| Открыта ли смена | `get_personal_session_info`, помощник `is_personal_session_open(emp, org, tg) -> bool` | `/api/1/employees/shift/is_open` | 10/мин |
| Где открыта смена курьера | `get_terminal_groups_of_employee` | `/api/1/employees/shifts/by_courier` | 10/мин |
| Места активных курьеров, история мест | `get_active_courier_locations`, `get_active_courier_locations_by_terminal`, `get_courier_location_history` | `/api/1/employees/couriers/active_location…`, `locations/by_time_offset` | 10/мин |
| Сотрудник по id | `get_employee` | `/api/employees/v1/employee/get` | 10/мин |
| Список сотрудников | `list_employees`, помощник `list_all_employees(filters=…, fields=…)` | `/api/employees/v1/employee/list` | 10/мин |
| Создать, изменить, уволить, вернуть | `create_employee`, `update_employee`, `fire_employees`, `restore_employee` | `/api/employees/v1/employee/*` | 100/мин |
| Должности | `get_employee_position`, `list_employee_positions` | `/api/employees/v1/positions/*` | 10/мин |
| Явки: список | `list_employee_attendances`, помощник `list_all_employee_attendances(org, start, end)` | `/api/employees/v1/attendance/list` | 10/мин |
| Явки: создать, изменить, удалить | `create_employee_attendance`, `update_employee_attendance`, `delete_employee_attendance` | `/api/employees/v1/attendance/*` | 100/мин |
| Типы явок | `list_employee_attendance_types` | `/api/employees/v1/attendance-type/list` | 10/мин |

Что важно знать:

- **Телефон.** В списке сотрудников он есть только если запрошен: без `fields` iiko отдаёт
  лишь `id`, `name`, `code`, `isFired`. `list_all_employees` по умолчанию просит
  `EMPLOYEE_CONTACT_FIELDS` (с `phone`) и обходит все страницы. В карточке
  `get_employee` и в `get_employee_info` телефон приходит всегда (если заполнен в iiko).
- **Явки.** Период — дата и время в ISO 8601 (например `2026-10-13T00:00:00Z`; проверено
  на стенде). iiko создаёт только закрытые явки (`endAt` обязателен); удаление необратимо;
  смена организации в `update_employee_attendance` даёт новую явку с новым id.
- **Смена.** Успешный ответ «открыта ли смена» iiko помечает `error: "NO_ERROR"` —
  `is_personal_session_open` считает его успехом, иное непустое `error` — исключение
  `RuntimeError`.
- **Расписания (графика смен) в облачном API iiko нет** — только явки.

### Номенклатура и отчёты (0.5.0)

- Техкарты v3: `create_…`, `update_…`, `delete_…`, `get_…`, `list_nomenclature_assembly_charts_v3`,
  `resolve_nomenclature_assembly_chart_v3` (вид на дату: `assembled`, `prepared`, `tree`);
  справочники: `list_nomenclature_discount_types`, `get_…`/`list_nomenclature_outer_economic_activity_code(s)`
  (коды ТН ВЭД). Чтение 10/мин, запись 100/мин.
- Отчёты `/api/reporting/v1`: `get_income_plan` (план выручки по дням, 10/мин),
  `list_olap_presets()` (сохранённые пресеты, 10/мин), `get_olap_preset_report` (данные
  пресета за период, 1/мин).

### Смена поведения с 0.4.x (клиент iikocloud 0.3.0, описание iiko 9.8.6.3)

- `list_inventory_incoming_invoices` / `list_inventory_outgoing_invoices` отдают
  `IncomingInvoiceListItem` / `OutgoingInvoiceListItem` (так теперь описан ответ iiko).
- `PayRequest` (оплата приходной накладной): поля `account_id`, `amount`, `payment_date`,
  `cfo_item_id` вместо `account_from`, `account_to`, `date`, `sum`.
- `GetCounteragentsRequest` без `organization_id` (справочник общий для ключа), с отбором
  `is_deleted` и `revision`; у `GetPriceListRequest` обязателен `counteragent_id`.
- Меню V3: `MenuV3OverrideTaxCategory` — поля `UUID | None` вместо строк; у вариантов
  модификатора (`ModifierItem`) все поля, кроме `id`, необязательны — пустое поле берётся из
  `MenuV3.modifiers` с тем же `id`.
- Обязательными стали: `code` у создания/изменения группы и продукта номенклатуры, `name` у
  `EmployeeCreateRequest`, `dateTo` у сохранения техкарт v1/v2, `number` у
  `IncomingInventoryUpdateRequest`.

## Тесты

```bash
# Unit-тесты (без сети)
uv run pytest -m unit -v

# Интеграционные (нужен config.test.yml и IIKOCLOUD_TEST_CONFIG)
uv run pytest -m integration -v

# Только read-эндпоинты, без write/lifecycle на стенде
uv run pytest -m "integration and not write" -v
```

## Линт и типы

Ruff и mypy входят в dev-зависимости (`uv sync` ставит их автоматически).

```bash
uv run ruff check .
uv run mypy iikocloud tests
```

- Ruff: `line-length = 92`, правила `E, F, I, UP, B, SIM` (`pyproject.toml`).
- mypy: `strict = true` для пакета `iikocloud`, плагин `pydantic.mypy`
  (иначе mypy требует camelCase-алиасы SDK в конструкторах моделей).
  Для `tests.*` strict ослаблен: без обязательных аннотаций вложенных
  helper'ов и с отключёнными `method-assign` / `union-attr` /
  `func-returns-value` — эти правила конфликтуют с идиоматикой моков
  (подмена методов менеджера, `await_args.args`, side_effect-заглушки).

Все интеграционные тесты помечены `slow` (каждый ходит в реальный API), поэтому `-m "integration and not slow"` не выберет ничего.

Для интеграционных тестов скопируйте `config.test.example.yml` → `config.test.yml` и задайте секции `read` / `write` с полными v2-тройками credentials. Без файла или env тесты пропускаются через `pytest.skip`.

**Write-секция / customer lifecycle:** credentials для `write` должны иметь доступ к Loyalty/CRM на организации стенда — иначе lifecycle-тесты (create/get/delete/restore) будут `pytest.skip` с пометкой о недоступности CRM.

**Нестабильные read-эндпоинты:** на части стендов `get_organization_settings` и `get_external_menu_by_id` недоступны или зависают, поэтому интеграционных тестов для них нет — они покрыты только unit-тестами. Добавляя их в интеграционный прогон, оборачивайте вызов в `pytest.skip`.
