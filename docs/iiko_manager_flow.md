# IikoCloudApiClientManager — Архитектура и поток запросов

## Описание

`IikoCloudApiClientManager` — это фасад для работы с iikocloud API, реализующий:
- **Multitone паттерн** — один экземпляр на каждый `key_id`
- **Автоматическое управление токенами** — получение и обновление Bearer-токенов
- **Per-method rate limiting** — ограничение частоты запросов по каждому методу API
- **Глобальный rate limiting** — общее ограничение всех запросов
- **Retry при 401** — автоматическое обновление токена при истечении

---

## Компоненты системы

```mermaid
graph TB
    subgraph "IikoCloudApiClientManager"
        MANAGER[IikoCloudApiClientManager<br/>Multitone: 1 экземпляр на key_id]
        TOKEN_MGR[TokenManager<br/>Управление Bearer-токенами]
        GLOBAL_RL[GlobalRateLimiter<br/>Singleton: общий лимит]
        METHOD_RL[TokenBucketRateLimiter<br/>Per-method лимиты]
        API_CLIENT[ApiClient<br/>HTTP клиент iikocloud]
    end

    subgraph "Внешние API"
        CUSTOMERS_API[CustomersApi]
        ORGS_API[OrganizationsApi]
        MENU_API[MenuApi]
        TERMINAL_API[TerminalGroupsApi]
        DICT_API[DictionariesApi]
    end

    CONFIG[IikoCloudConfig<br/>YAML конфигурация]

    CONFIG --> MANAGER
    MANAGER --> TOKEN_MGR
    MANAGER --> GLOBAL_RL
    MANAGER --> METHOD_RL
    MANAGER --> API_CLIENT
    API_CLIENT --> CUSTOMERS_API
    API_CLIENT --> ORGS_API
    API_CLIENT --> MENU_API
    API_CLIENT --> TERMINAL_API
    API_CLIENT --> DICT_API

    classDef manager fill:#2d3748,stroke:#4a5568,color:#fff
    classDef limiter fill:#319795,stroke:#2c7a7b,color:#fff
    classDef api fill:#1a202c,stroke:#4a5568,color:#fff

    class MANAGER,TOKEN_MGR manager
    class GLOBAL_RL,METHOD_RL limiter
    class CUSTOMERS_API,ORGS_API,MENU_API,TERMINAL_API,DICT_API,API_CLIENT api
```

---

## Инициализация менеджера

При первом использовании менеджер создаётся через `get_instance()` или `from_config()`:

```mermaid
flowchart TD
    START(["Запрос get_instance(credentials)"]) 
    
    CHECK_LOCK{"Lock создан?"}
    CREATE_LOCK["Создать asyncio.Lock"]
    ACQUIRE_LOCK["Захватить lock"]
    
    CHECK_INSTANCE{"Экземпляр для key_id существует?"}
    RETURN_EXISTING["Вернуть существующий экземпляр"]
    
    CREATE_LIMITS["Создать MethodRateLimits<br/>(из config или default)"]
    COMPUTE_GLOBAL["Вычислить глобальный лимит<br/>(самый свободный из всех методов)"]
    CREATE_GLOBAL_RL["Создать GlobalRateLimiter"]
    CREATE_INSTANCE["Создать IikoCloudApiClientManager"]
    SAVE_INSTANCE["Сохранить в _instances[key_id]"]
    RETURN_NEW["Вернуть новый экземпляр"]

    START --> CHECK_LOCK
    CHECK_LOCK -->|Нет| CREATE_LOCK --> ACQUIRE_LOCK
    CHECK_LOCK -->|Да| ACQUIRE_LOCK
    
    ACQUIRE_LOCK --> CHECK_INSTANCE
    CHECK_INSTANCE -->|Да| RETURN_EXISTING
    CHECK_INSTANCE -->|Нет| CREATE_LIMITS
    
    CREATE_LIMITS --> COMPUTE_GLOBAL
    COMPUTE_GLOBAL --> CREATE_GLOBAL_RL
    CREATE_GLOBAL_RL --> CREATE_INSTANCE
    CREATE_INSTANCE --> SAVE_INSTANCE
    SAVE_INSTANCE --> RETURN_NEW

    classDef process fill:#2d3748,stroke:#4a5568,color:#fff
    classDef decision fill:#1a202c,stroke:#4a5568,color:#fff
    classDef terminator fill:#319795,stroke:#2c7a7b,color:#fff
    
    class START,RETURN_EXISTING,RETURN_NEW terminator
    class CHECK_LOCK,CHECK_INSTANCE decision
    class CREATE_LOCK,ACQUIRE_LOCK,CREATE_LIMITS,COMPUTE_GLOBAL,CREATE_GLOBAL_RL,CREATE_INSTANCE,SAVE_INSTANCE process
```

---

## Основной поток выполнения запроса

Каждый вызов API-метода проходит через `execute_with_retry()`:

```mermaid
flowchart TD
    START(["Вызов API метода<br/>(например, get_customer_info)"])
    
    subgraph INIT ["1. Инициализация токена"]
        ENSURE_TOKEN["ensure_token_with_limits()"]
        HAS_TOKEN{"Токен есть?"}
        GET_NEW_TOKEN["Получить новый токен"]
        SET_TOKEN["Установить токен в ApiClient"]
    end
    
    subgraph RATE_LIMIT ["2. Rate Limiting"]
        ACQUIRE_GLOBAL["Ждать глобальный лимит<br/>GlobalRateLimiter.acquire()"]
        ACQUIRE_METHOD["Ждать лимит метода<br/>TokenBucketRateLimiter.acquire()"]
    end
    
    subgraph EXECUTE ["3. Выполнение запроса"]
        API_CALL["Вызов iikocloud API"]
        CHECK_RESPONSE{"Результат?"}
    end
    
    subgraph RETRY ["4. Обработка 401"]
        REFRESH_TOKEN["Обновить токен"]
        RETRY_LIMITS["Снова пройти rate limits"]
        RETRY_CALL["Повторить вызов API"]
    end
    
    SUCCESS(["Вернуть результат"])
    ERROR(["Выбросить исключение"])

    START --> ENSURE_TOKEN
    ENSURE_TOKEN --> HAS_TOKEN
    HAS_TOKEN -->|Да| ACQUIRE_GLOBAL
    HAS_TOKEN -->|Нет| GET_NEW_TOKEN
    GET_NEW_TOKEN --> SET_TOKEN
    SET_TOKEN --> ACQUIRE_GLOBAL
    
    ACQUIRE_GLOBAL --> ACQUIRE_METHOD
    ACQUIRE_METHOD --> API_CALL
    
    API_CALL --> CHECK_RESPONSE
    CHECK_RESPONSE -->|Успех| SUCCESS
    CHECK_RESPONSE -->|401 Unauthorized| REFRESH_TOKEN
    CHECK_RESPONSE -->|Другая ошибка| ERROR
    
    REFRESH_TOKEN --> RETRY_LIMITS
    RETRY_LIMITS --> RETRY_CALL
    RETRY_CALL --> SUCCESS

    classDef process fill:#2d3748,stroke:#4a5568,color:#fff
    classDef decision fill:#1a202c,stroke:#4a5568,color:#fff
    classDef terminator fill:#319795,stroke:#2c7a7b,color:#fff
    classDef error fill:#9b2c2c,stroke:#742a2a,color:#fff
    
    class START,SUCCESS terminator
    class ERROR error
    class HAS_TOKEN,CHECK_RESPONSE decision
    class ENSURE_TOKEN,GET_NEW_TOKEN,SET_TOKEN,ACQUIRE_GLOBAL,ACQUIRE_METHOD,API_CALL,REFRESH_TOKEN,RETRY_LIMITS,RETRY_CALL process
```

---

## Rate Limiting: Token Bucket алгоритм

Каждый метод API имеет собственный rate limiter с конфигурируемыми параметрами:

```mermaid
flowchart TD
    REQUEST(["Запрос на acquire()"])
    LOCK["Захватить asyncio.Lock"]
    REFILL["Пополнить токены<br/>(пропорционально прошедшему времени)"]
    CHECK_TOKENS{"tokens >= 1?"}
    CALCULATE_WAIT["Вычислить время ожидания:<br/>wait = (1 - tokens) / refill_rate"]
    SLEEP["asyncio.sleep(wait_time)"]
    CONSUME["tokens -= 1"]
    RELEASE["Освободить lock"]
    DONE(["Разрешить запрос"])

    REQUEST --> LOCK
    LOCK --> REFILL
    REFILL --> CHECK_TOKENS
    CHECK_TOKENS -->|Да| CONSUME
    CHECK_TOKENS -->|Нет| CALCULATE_WAIT
    CALCULATE_WAIT --> SLEEP
    SLEEP --> REFILL
    CONSUME --> RELEASE
    RELEASE --> DONE

    classDef process fill:#2d3748,stroke:#4a5568,color:#fff
    classDef decision fill:#1a202c,stroke:#4a5568,color:#fff
    classDef terminator fill:#319795,stroke:#2c7a7b,color:#fff
    
    class REQUEST,DONE terminator
    class CHECK_TOKENS decision
    class LOCK,REFILL,CALCULATE_WAIT,SLEEP,CONSUME,RELEASE process
```

### Формула пополнения токенов

```
tokens_to_add = elapsed_time × (max_requests / time_window_seconds)
tokens = min(max_tokens, tokens + tokens_to_add)
```

---

## Управление токенами (TokenManager)

`TokenManager` обеспечивает потокобезопасное получение и обновление Bearer-токенов:

```mermaid
flowchart TD
    subgraph "ensure_token_with_limits()"
        E_START(["Запрос токена"])
        E_CHECK{"token != None?"}
        E_RETURN(["Использовать существующий"])
        E_LOCK["Захватить lock"]
        E_DOUBLE_CHECK{"token != None?<br/>(double-check)"}
        E_CLEAR_EVENT["refresh_event.clear()"]
        E_FETCH["Запросить токен от API"]
        E_SET["Установить токен в ApiClient"]
        E_SET_EVENT["refresh_event.set()"]
        
        E_START --> E_CHECK
        E_CHECK -->|Да| E_RETURN
        E_CHECK -->|Нет| E_LOCK
        E_LOCK --> E_DOUBLE_CHECK
        E_DOUBLE_CHECK -->|Да| E_RETURN
        E_DOUBLE_CHECK -->|Нет| E_CLEAR_EVENT
        E_CLEAR_EVENT --> E_FETCH
        E_FETCH --> E_SET
        E_SET --> E_SET_EVENT
        E_SET_EVENT --> E_RETURN
    end

    subgraph "refresh_token_if_401_with_limits()"
        R_START(["Получена 401 ошибка"])
        R_IS_401{"Это 401?"}
        R_FALSE(["return False"])
        R_CHECK_EVENT{"refresh_event.is_set()?"}
        R_WAIT["Ждать refresh_event"]
        R_TRUE(["return True"])
        R_LOCK["Захватить lock"]
        R_VERSION_CHECK{"version изменилась?"}
        R_CLEAR["refresh_event.clear()"]
        R_FETCH["Запросить новый токен"]
        R_UPDATE["Обновить token и version"]
        R_SET_EVENT["refresh_event.set()"]
        
        R_START --> R_IS_401
        R_IS_401 -->|Нет| R_FALSE
        R_IS_401 -->|Да| R_CHECK_EVENT
        R_CHECK_EVENT -->|Нет| R_WAIT
        R_WAIT --> R_TRUE
        R_CHECK_EVENT -->|Да| R_LOCK
        R_LOCK --> R_VERSION_CHECK
        R_VERSION_CHECK -->|Да| R_TRUE
        R_VERSION_CHECK -->|Нет| R_CLEAR
        R_CLEAR --> R_FETCH
        R_FETCH --> R_UPDATE
        R_UPDATE --> R_SET_EVENT
        R_SET_EVENT --> R_TRUE
    end

    classDef process fill:#2d3748,stroke:#4a5568,color:#fff
    classDef decision fill:#1a202c,stroke:#4a5568,color:#fff
    classDef terminator fill:#319795,stroke:#2c7a7b,color:#fff
    
    class E_START,E_RETURN,R_START,R_FALSE,R_TRUE terminator
    class E_CHECK,E_DOUBLE_CHECK,R_IS_401,R_CHECK_EVENT,R_VERSION_CHECK decision
```

### Механизм защиты от гонок

1. **Lock** — только одна корутина может обновлять токен
2. **Event** — другие корутины ждут `refresh_event` вместо повторных запросов
3. **Version** — проверка, не обновил ли кто-то токен пока мы ждали lock

---

## Лимиты по методам API

| Метод | max_requests | time_window | Описание |
|-------|-------------|-------------|----------|
| `auth` | 1 | 5 сек | Авторизация |
| `get_organizations` | 1 | 10 сек | Список организаций |
| `create_or_update_customer` | 100 | 60 сек | Создание/обновление клиента |
| `get_customer_info` | 100 | 60 сек | Информация о клиенте |
| `delete_customers` | 100 | 60 сек | Удаление клиентов |
| `restore_customers` | 100 | 60 сек | Восстановление клиентов |
| `get_terminal_groups` | 10 | 60 сек | Терминальные группы |
| `check_terminal_groups_alive` | 10 | 60 сек | Проверка доступности |
| `get_external_menus` | 1 | 1800 сек | Список внешних меню |
| `get_menu_by_id` | 5 | 60 сек | Меню по ID |
| `get_stop_lists` | 10 | 60 сек | Стоп-листы |
| `get_delivery_cancel_causes` | 1 | 60 сек | Причины отмены |
| `get_order_types` | 1 | 60 сек | Типы заказов |
| `get_payment_types` | 1 | 60 сек | Типы платежей |
| `get_discounts` | 1 | 60 сек | Скидки |
| `get_removal_types` | 1 | 60 сек | Типы удаления |

> **Глобальный лимит** вычисляется автоматически как самый "свободный" из всех методов (максимальная скорость запросов).

---

## Пример использования

```python
import asyncio
from iikocloud import IikoCloudApiClientManager, get_iikocloud_config

async def main():
    # 1. Загрузить конфигурацию из YAML
    config = get_iikocloud_config()
    
    # 2. Создать менеджер (Multitone — повторный вызов вернёт тот же экземпляр)
    manager = await IikoCloudApiClientManager.from_config(config)
    
    try:
        # 3. Вызвать API-метод
        # Автоматически:
        #   - Получит токен (если нет)
        #   - Применит rate limiting
        #   - Обновит токен при 401
        orgs = await manager.organizations()
        print(orgs)
        
        # 4. Другой метод — те же гарантии
        customer = await manager.get_customer_by_phone(
            phone="+79001234567",
            organization_id="org-uuid-here"
        )
        print(customer)
        
    finally:
        # 5. Закрыть все соединения
        await IikoCloudApiClientManager.close_all()

asyncio.run(main())
```

---

## Обработка ошибок

| Код ответа | Поведение менеджера |
|------------|---------------------|
| **200** | Вернуть результат |
| **401** | Обновить токен и повторить запрос (1 раз) |
| **429** | Rate limit от iiko — можно проверить через `is_locked_because_of_iikocloud_rate_limit()` |
| **4xx/5xx** | Выбросить исключение (логируется) |

### Исключения

- `IikoCloudAuthException` — ошибка авторизации (некорректный API-ключ)
- `ApiException` — ошибки API iikocloud
- `UnauthorizedException` — 401 ошибка (обрабатывается автоматически)

---

## Закрытие соединений

При завершении работы **обязательно** вызвать:

```python
await IikoCloudApiClientManager.close_all()
```

Это:
1. Закроет все HTTP-соединения
2. Сбросит все экземпляры менеджеров
3. Сбросит `GlobalRateLimiter`
4. Очистит `TokenManager`
