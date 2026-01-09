# Процесс регистрации пользователя

## Описание

Данная диаграмма описывает алгоритм регистрации нового пользователя по номеру телефона.

## Основной поток

POST /users/register

```mermaid
flowchart TD
    START(["Старт"])
    VALIDATE["Проверить валидность данных"]
    EXISTS_IN_DB{"Пользователь уже существует в БД?"}
    CREATE_IIKO["Создать пользователя в iiko"]
    IIKO_SUCCESS{"Создан успешно в iiko?"}
    SAVE_DB["Сохранить пользователя в БД"]
    RETURN_SUCCESS["Вернуть успешный ответ"]
    RETURN_CONFLICT["Вернуть ошибку 409 (Пользователь существует)"]
    RETURN_BAD_DATA["Вернуть ошибку 400 (Некорректные данные)"]
    RETURN_FAILED["Вернуть ошибку 500 (Ошибка регистрации)"]

    START --> VALIDATE
    VALIDATE -- "OK" --> EXISTS_IN_DB
    VALIDATE -- "Некорректные данные" --> RETURN_BAD_DATA

    EXISTS_IN_DB -- "Да" --> RETURN_CONFLICT
    EXISTS_IN_DB -- "Нет" --> CREATE_IIKO

    CREATE_IIKO --> IIKO_SUCCESS
    IIKO_SUCCESS -- "Да" --> SAVE_DB
    IIKO_SUCCESS -- "Нет" --> RETURN_FAILED

    SAVE_DB --> RETURN_SUCCESS

    %% Стили
    classDef process fill:#2d3748,stroke:#4a5568,color:#fff;
    classDef decision fill:#1a202c,stroke:#4a5568,color:#fff;
    classDef terminator fill:#319795,stroke:#2c7a7b,color:#fff;
    class START,RETURN_SUCCESS,RETURN_CONFLICT,RETURN_BAD_DATA,RETURN_FAILED terminator;
    class VALIDATE,CREATE_IIKO,SAVE_DB process;
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

