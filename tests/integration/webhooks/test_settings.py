"""Danger_write-тест Webhooks (write-секция).

get (сохранить исходные) -> update (тестовый URI) -> get (проверка)
-> update обратно (finally) -> get (проверка восстановления).
auth_token НЕ выводим в логи.

Сервер жёстко лимитирует update_webhook_settings: 429 при повторном
update внутри серверного окна. Окно эмпирически длинное (замерено >16 мин,
возможно ~1 ч) — оба update идут через _update_with_retry с бюджетом
~58 мин на вызов. Полный прогон в худшем случае занимает ~1 ч.

Запуск:
    uv run pytest tests/integration/webhooks -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    GetWebHookSettingsRequest,
    UpdateWebHookSettingsRequest,
)
from iikocloud_client.exceptions import ApiException

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0
_TEST_URI = "https://example.com/iikocloud-manager-test-hook"
_UPDATE_ATTEMPTS = 35
_UPDATE_RETRY_SEC = 100.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


async def _update_with_retry(
    manager: IikoCloudApiClientManager,
    request: UpdateWebHookSettingsRequest,
) -> None:
    """update_webhook_settings с retry на серверный 429.

    Серверное окно лимита update намного длиннее клиентского 1/60s
    (эмпирически >16 мин): повторный update даже через минуту получает
    429. Ретраим с паузой 100s; бюджет 35 попыток покрывает окно ~1 ч.
    """
    for attempt in range(_UPDATE_ATTEMPTS):
        try:
            await manager.update_webhook_settings(request)
            return
        except ApiException as exc:
            if exc.status == 429 and attempt < _UPDATE_ATTEMPTS - 1:
                logger.info(
                    "update_webhook_settings: 429, retry %d/%d через %.0fs",
                    attempt + 1,
                    _UPDATE_ATTEMPTS,
                    _UPDATE_RETRY_SEC,
                )
                await asyncio.sleep(_UPDATE_RETRY_SEC)
                continue
            raise


class TestWebhookSettings:
    async def test_update_and_restore_settings(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        # 1. Сохранить исходные настройки (auth_token не логируем)
        original = await manager.get_webhook_settings(
            GetWebHookSettingsRequest(organization_id=organization_id)
        )
        assert original is not None

        if not original.web_hooks_uri:
            pytest.skip("Webhook не настроен на стенде — нечего восстанавливать")

        updated = False
        try:
            # 2. Тестовый URI
            await _update_with_retry(
                manager,
                UpdateWebHookSettingsRequest(
                    organization_id=organization_id,
                    web_hooks_uri=_TEST_URI,
                    auth_token=original.auth_token,
                    web_hooks_filter=original.web_hooks_filter,
                ),
            )
            updated = True

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. Проверка применения
            current = await manager.get_webhook_settings(
                GetWebHookSettingsRequest(organization_id=organization_id)
            )
            assert current.web_hooks_uri == _TEST_URI

        finally:
            # 4. Восстановление исходных значений + проверка восстановления.
            # Провал восстановления — FAIL теста, а не тихий pass:
            # стенд не должен оставаться с тестовым URI незамеченным.
            if updated:
                await asyncio.sleep(_API_PAUSE_SEC)
                try:
                    await _update_with_retry(
                        manager,
                        UpdateWebHookSettingsRequest(
                            organization_id=organization_id,
                            web_hooks_uri=original.web_hooks_uri,
                            auth_token=original.auth_token,
                            web_hooks_filter=original.web_hooks_filter,
                        ),
                    )
                    await asyncio.sleep(_API_PAUSE_SEC)
                    restored = await manager.get_webhook_settings(
                        GetWebHookSettingsRequest(organization_id=organization_id)
                    )
                    if restored.web_hooks_uri != original.web_hooks_uri:
                        raise RuntimeError(
                            "Восстановление webhook не подтвердилось: "
                            "URI после restore не совпадает с исходным"
                        )
                except Exception as exc:
                    logger.error(
                        "ВОССТАНОВЛЕНИЕ WEBHOOK НЕ УДАЛОСЬ для org %s: %s",
                        organization_id,
                        exc,
                    )
                    raise
