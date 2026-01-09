# Процесс регистрации пользователя

## Описание

Данная диаграмма описывает алгоритм регистрации нового пользователя по номеру телефона.

## Основной поток

POST /users/register

```mermaid
flowchart TD
    START(["Старт"])
    VALIDATE{"Валидны ли данные?"}
    EXISTS_IN_DB{"Пользователь уже существует в БД?"}
    RETURN_SUCCESS["Вернуть успешный ответ"]
    RETURN_CONFLICT["Вернуть ошибку 409 (Пользователь существует)"]
    RETURN_BAD_DATA["Вернуть ошибку 400 (Некорректные данные)"]
    CREATE_USER_IN_DB["Создать пользователя в БД"]
    PLACE_EVENT_USER_REGISTERED["Создать событие регистрации пользователя"]
    START --> VALIDATE
    VALIDATE -- "Да" --> EXISTS_IN_DB
    VALIDATE -- "Нет" --> RETURN_BAD_DATA

    EXISTS_IN_DB -- "Да" --> RETURN_CONFLICT
    EXISTS_IN_DB -- "Нет" --> CREATE_USER_IN_DB

    CREATE_USER_IN_DB --> PLACE_EVENT_USER_REGISTERED --> RETURN_SUCCESS

    subgraph SUBPROCESS ["Пользователь зарегистрирован"]
        GET_FROM_IIKO["Получить данные о пользователе из iiko"]
        SAVE_IN_IIKO["Сохранить в БД"]
        CREATE_IN_IIKO["Создать пользователя в iiko"]
        EXISTS_IN_IIKO{"Данные есть в iiko?"}
        SAVE_EVENT_NOT_HANDLED["Отметить событие необработанным"]
        GET_FROM_IIKO --> EXISTS_IN_IIKO
        EXISTS_IN_IIKO -- "Да" --> SAVE_IN_IIKO
        EXISTS_IN_IIKO -- "Нет" --> CREATE_IN_IIKO
        EXISTS_IN_IIKO -- "Нет ответа от iiko" --> SAVE_EVENT_NOT_HANDLED
        CREATE_IN_IIKO --> CREATE_IN_IIKO_SUCCESS
        
        CREATE_IN_IIKO_SUCCESS{Создан в iiko успешно?}
        CREATE_IN_IIKO_SUCCESS -- "Да" --> GET_FROM_IIKO
        CREATE_IN_IIKO_SUCCESS -- "Нет" --> SAVE_EVENT_NOT_HANDLED

    end

    %% Стили
    classDef process fill:#2d3748,stroke:#4a5568,color:#fff;
    classDef decision fill:#1a202c,stroke:#4a5568,color:#fff;
    classDef terminator fill:#319795,stroke:#2c7a7b,color:#fff;
    class START,RETURN_SUCCESS,RETURN_CONFLICT,RETURN_BAD_DATA,RETURN_FAILED terminator;
    class VALIDATE,CREATE_IIKO,SAVE_DB,CREATE_USER_IN_DB,PLACE_EVENT_USER_REGISTERED process;
    class EXISTS_IN_DB,IIKO_SUCCESS decision;
```

Успех
```json
{
    "id": "",
    "name": "",
    "last_name": "",
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
    "lastProcessedOrderDate": "",
    "firstOrderDate": "",
    "lastVisitedOrganizationId": "",
    "registrationOrganizationId": ""
}
```

