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

## Тесты

```bash
# Unit-тесты (без сети)
uv run pytest -m unit -v

# Интеграционные (нужен config.test.yml и IIKOCLOUD_TEST_CONFIG)
uv run pytest -m integration -v

# Без медленных интеграционных
uv run pytest -m "integration and not slow" -v
```

Для интеграционных тестов скопируйте `config.test.example.yml` → `config.test.yml` и задайте секции `read` / `write` с полными v2-тройками credentials. Без файла или env тесты пропускаются через `pytest.skip`.
