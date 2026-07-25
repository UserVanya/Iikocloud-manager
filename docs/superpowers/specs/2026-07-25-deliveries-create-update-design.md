# Спека: модуль deliveries_create_and_update

Дата: 2026-07-25
Статус: утверждена (brainstorm с пользователем)
Родительская спека: `2026-07-23-full-sdk-coverage-design.md`

## 1. Scope

Обёртки над `DeliveriesCreateAndUpdateApi` SDK — **20 методов** (все, кроме
deprecated `update_delivery_order_courier` и `update_delivery_order_payments`).

### Методы

| Метод | Endpoint | Request → Response |
|---|---|---|
| `create_delivery_order` | `/api/1/deliveries/create` | `CreateOrderRequest` → `OrderResponse` |
| `add_delivery_order_items` | `/api/1/deliveries/add_items` | `AddOrderItemsRequest` → `CorrelationIdResponse` |
| `add_delivery_order_payments` | `/api/1/deliveries/add_payments` | `AddOrderPaymentsRequest` → `CorrelationIdResponse` |
| `cancel_delivery_order` | `/api/1/deliveries/cancel` | `CancelOrderRequest` → `CorrelationIdResponse` |
| `cancel_delivery_confirmation` | `/api/1/deliveries/cancel_confirmation` | `CancelDeliveryConfirmationRequest` → `CorrelationIdResponse` |
| `confirm_delivery` | `/api/1/deliveries/confirm` | `ConfirmDeliveryRequest` → `CorrelationIdResponse` |
| `change_delivery_comment` | `/api/1/deliveries/change_comment` | `ChangeDeliveryCommentRequest` → `CorrelationIdResponse` |
| `change_delivery_complete_before` | `/api/1/deliveries/change_complete_before` | `ChangeCompleteBeforeRequest` → `CorrelationIdResponse` |
| `change_delivery_driver_info` | `/api/1/deliveries/change_driver_info` | `ChangeDriverInfoRequest` → `CorrelationIdResponse` |
| `change_delivery_external_data` | `/api/1/deliveries/change_external_data` | `ChangeExternalDataRequest` → `CorrelationIdResponse` |
| `change_delivery_operator` | `/api/1/deliveries/change_operator` | `ChangeDeliveryOperatorRequest` → `CorrelationIdResponse` |
| `change_delivery_payments` | `/api/1/deliveries/change_payments` | `ChangePaymentsRequest` → `CorrelationIdResponse` |
| `change_delivery_point` | `/api/1/deliveries/change_delivery_point` | `ChangeDeliveryPointRequest` → `CorrelationIdResponse` |
| `change_delivery_service_type` | `/api/1/deliveries/change_service_type` | `ChangeServiceTypeRequest` → `CorrelationIdResponse` |
| `close_delivery_order` | `/api/1/deliveries/close` | `CloseDeliveryOrderRequest` → `CorrelationIdResponse` |
| `print_delivery_bill` | `/api/1/deliveries/print_delivery_bill` | `PrintDeliveryBillRequest` → `CorrelationIdResponse` |
| `print_table_order_bill` | `/api/1/order/print_bill` | `PrintBillRequest` → `CorrelationIdResponse` |
| `update_delivery_order_problem` | `/api/1/deliveries/update_order_problem` | `UpdateOrderProblemRequest` → `CorrelationIdResponse` |
| `update_delivery_order_status` | `/api/1/deliveries/update_order_delivery_status` | `UpdateDeliveryStatusRequest` → `CorrelationIdResponse` |
| `update_delivery_tracking_link` | `/api/1/deliveries/update_tracking_link` | `UpdateTrackingLinkRequest` → `None` |

Особенности:
- Только `create_delivery_order` возвращает `OrderResponse` (с
  `order_info.creation_status`: Success/InProgress/Error); остальные —
  асинхронные команды (`CorrelationIdResponse`), статус исполнения через
  `/api/1/commands/status` (покрытие — отдельный модуль Operations).
- `update_delivery_tracking_link` — единственный с ответом без тела → `None`.
- Во всех request-моделях одиночный обязательный `organization_id`.
- Физического удаления заказа нет — cleanup только через `cancel`.

## 2. Конвенция сигнатур

Как везде: core принимает SDK request-модель целиком, возвращает SDK
response-модель (`None` для `update_delivery_tracking_link`).

## 3. Helpers (решение пользователя — пишем в этом модуле)

- `build_product_item(product_id, price, amount=1.0, *, product_size_id=None,
  comment=None, modifiers=None) -> DeliveryOrderCreateProductItem` —
  конструктор позиции с дискриминатором `type="Product"`.
- `build_compound_item(primary_product_id, *, secondary_product_id=None,
  amount=1.0, price, common_modifiers=None, comment=None)
  -> DeliveryOrderCreateCompoundItem` — конструктор составной позиции
  (`type="Compound"`), собирает `DeliveryOrderCreateCompoundItemComponent`
  внутри. Точная сигнатура фиксируется в плане по модели SDK.
- `cancel_order(organization_id, order_id, cancel_comment=None)
  -> CorrelationIdResponse` — короткая форма `cancel_delivery_order`
  (str/UUID на вход, сборка `CancelOrderRequest` внутри).

`create_simple_delivery_order` НЕ делаем (однопозиционный заказ бесполезен;
заказ собирается как core + item-builders).

## 4. Файловая структура

- `iikocloud/mixins/deliveries/__init__.py` — новый домен
- `iikocloud/mixins/deliveries/core.py` — `DeliveriesCoreMixin` (20 методов)
- `iikocloud/mixins/deliveries/helpers.py` — `DeliveriesHelpersMixin`
  (3 helpers из §3)
- `iikocloud/mixins/_base.py` — lazy-геттер `get_deliveries_create_and_update_api`,
  20 значений `ApiMethod`, 20 полей `MethodRateLimits`
- `iikocloud/api_client_manager.py` — регистрация `DeliveriesHelpersMixin`
- `iikocloud/config_reader.py` + `config.example.yml` — 20 лимитов
- Тесты: `tests/unit/test_deliveries.py`,
  `tests/integration/deliveries/__init__.py`,
  `tests/integration/deliveries/test_write.py`

## 5. Rate limits

- `create_delivery_order` — **20 / 60 s** (решение пользователя)
- остальные 19 команд — **100 / 60 s**

## 6. Тесты

### Unit (моки SDK, паттерн `tests/unit/test_menu.py`)

Все 20 core-методов: делегирование в SDK с request-моделью, проксирование
ответа, `None` для tracking_link. Helpers: сборка моделей с правильными
дискриминаторами/вложенными компонентами, `cancel_order` собирает
`CancelOrderRequest`.

### Integration danger_write (секция `write`, маркер `danger_write`)

Полный цикл по живому заказу на write-стенде:

1. Гард: терминальная группа `is_alive` (как в стоп-листах) — иначе skip
   с явной причиной. Также skip при `is_alive=False` фронта.
2. `create_delivery_order`: один реальный продукт из номенклатуры
   (через `build_product_item`), тестовый телефон, без оплат;
   проверка `correlation_id` + `creation_status` in (Success, InProgress);
   при `Error` — fail с `error_info`.
3. change_* по живому заказу: `change_delivery_comment`,
   `change_delivery_complete_before` — проверка `correlation_id`.
4. Cleanup: `cancel_delivery_order` (через helper `cancel_order`) в `finally`
   — заказ остаётся в истории со статусом Cancelled, это норма.

Остальные 17 команд — только unit (прогон каждой по живому заказу требует
специфических состояний/прав; включаем точечно позже при потребности).

## 7. Открытые точки (решаются при реализации)

- Поведение стенда при create без payments и без terminal_group_id —
  если create падает, добавить минимально необходимые поля (фиксируем
  в отчёте задачи).
- `creation_status = InProgress` — верификация ограничивается приёмом
  команды (polling статуса — модуль Operations, позже).
- Точная сигнатура `build_compound_item` — по модели
  `DeliveryOrderCreateCompoundItemComponent`.

## 8. Definition of done

- 20 методов core + 3 helpers, `ApiMethod`, rate limits, config.example.yml,
  регистрация в менеджере.
- Unit зелёные (включая существующие 95), ruff+mypy чистые.
- Integration danger_write: create→change→cancel прогнан живьём (или skip
  с зафиксированной причиной стенда).
