# Процесс получения пользователя по номеру телефона

## Описание

Данная диаграмма описывает алгоритм поведения апи при запросе пользователя по phone или id.

## Основной поток

/users/by/id?{userId}
/users/by/phone?{userPhone}
```mermaid
flowchart TD
    %% Основной процесс
    CACHE{Есть ли в кэше?}
    ACTUAL_DATA[Вернуть актуальные данные]
    LAST_SAVED_DATA[Вернуть последние сохраненные данные]
    NO_DATA[Вернуть 404]
    TEMPORAL_ERROR[Вернуть 404 с iiko cloud server error]
    RETURN_DATA_FOUND_BUT_USER_NOT_REGISTERED[Вернуть 404 с пояснением: Пользователь существует в iiko, но не зарегистрирован на сайте]
    GET_FROM_CACHE[Получить данные из кэша]
    GET_DATA_FROM_IIKO[Получить данные из iiko]
    GET_DATA_FROM_DB[Получить данные из БД]
    GET_FROM_CACHE --> CACHE
    CACHE -->|Да| LAST_SAVED_DATA
    CACHE -->|Нет| GET_DATA_FROM_DB --> GET_DATA_FROM_IIKO -->DB
    DB{Есть ли в БД?}
    
    DB -->|Да| IIKO_REQUEST
    DB -->|Нет| IIKO
    
    IIKO{"Есть ли в iiko?"}
    IIKO -->|Есть| RETURN_DATA_FOUND_BUT_USER_NOT_REGISTERED
    IIKO -->|Нет данных о пользователе| NO_DATA
    IIKO -->|ошибка соединения с сервером iiko| TEMPORAL_ERROR

    SAVE --> ACTUAL_DATA
    RETURN_CONNECTION_ERROR --> LAST_SAVED_DATA
    %% Подпроцесс обновления данных из iiko
    IIKO_REQUEST{Есть ли в iiko?}
    IIKO_REQUEST -->|Ответ есть| SAVE[Обновить запись в<br>БД и обновить кэш]
    IIKO_REQUEST -->|Ответа нет| RETURN_CONNECTION_ERROR[Залогировать ошибку<br>обновления и запланировать ее на время позже]

    %% Стили
    classDef process fill:#2d3748,stroke:#4a5568,color:#fff
    classDef decision fill:#1a202c,stroke:#4a5568,color:#fff
    classDef subprocess fill:#1a202c,stroke:#4a5568,color:#fff,stroke-dasharray: 5 5
    
    class START,SAVE,UPDATE_PROCESS,UPDATE_DB,RETURN_CONNECTION_ERROR process
    class CACHE,DB,IIKO,IIKO_REQUEST decision
```

Success
```json
{
    "id": "",
    "name": "",
    "last_name":"",
    "middle_name": "",
    "tg_id": "",
    "email": "",
    "birthday": "",
    "comment": "",
    "consentStatus": "",
    "cardIds": "",
    "categoryIds": "",
    "walletIds": "",
    "shouldReceivePromoActionsInfo": "",
    "consentId": "",
    "isDeleted": "",
    "whenRegistered": "",
    "lastProcessedOrderDate":"",
    "firstOrderDate":"",
    "lastVisitedOrganizationId":"",
    "registrationOrganizationId":""
}
```

