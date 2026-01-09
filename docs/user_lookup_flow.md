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
    TEMPORAL_ERROR[Вернуть server error]
    
    CACHE -->|Да| LAST_SAVED_DATA
    CACHE -->|Нет| DB{Есть ли в БД?}
    
    DB -->|Да| UPDATE_PROCESS[Запустить процесс<br>обновления данных<br>из iiko о пользователе]
    DB -->|Нет| IIKO{Есть ли в iiko?}
    
    IIKO -->|Есть| SAVE[Обновить запись в<br>БД и обновить кэш]
    IIKO -->|Нет данных о пользователе| NO_DATA
    IIKO -->|ошибка соединения с сервером iiko| TEMPORAL_ERROR

    SAVE --> ACTUAL_DATA
    UPDATE_PROCESS --> SUBPROCESS
    RETURN_CONNECTION_ERROR --> LAST_SAVED_DATA
    %% Подпроцесс обновления данных из iiko
    subgraph SUBPROCESS [Обновление данных из iiko о пользователе]
        IIKO_REQUEST{Есть ли в iiko?}
        IIKO_REQUEST -->|Ответ есть| SAVE[Обновить запись в<br>БД и обновить кэш]
        IIKO_REQUEST -->|Ответа нет| RETURN_CONNECTION_ERROR[Залогировать ошибку<br>обновления и запланировать ее на время позже]
    end

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

