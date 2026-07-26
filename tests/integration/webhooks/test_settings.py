"""Danger_write-тест Webhooks (write-секция).

get (сохранить исходные) -> update (тестовый URI) -> get (проверка)
-> update обратно (finally). auth_token НЕ выводим в логи.

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

from iikocloud import IikoCloudApiClientManager

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0
_TEST_URI = "https://example.com/iikocloud-manager-test-hook"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


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
            update_response = await manager.update_webhook_settings(
                UpdateWebHookSettingsRequest(
                    organization_id=organization_id,
                    web_hooks_uri=_TEST_URI,
                    auth_token=original.auth_token,
                    web_hooks_filter=original.web_hooks_filter,
                )
            )
            assert update_response is not None
            updated = True

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. Проверка применения
            current = await manager.get_webhook_settings(
                GetWebHookSettingsRequest(organization_id=organization_id)
            )
            assert current.web_hooks_uri == _TEST_URI

        finally:
            # 4. Восстановление исходных значений
            if updated:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.update_webhook_settings(
                        UpdateWebHookSettingsRequest(
                            organization_id=organization_id,
                            web_hooks_uri=(
                                original.web_hooks_uri or "https://example.com/"
                            ),
                            auth_token=original.auth_token,
                            web_hooks_filter=original.web_hooks_filter,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "ВОССТАНОВЛЕНИЕ WEBHOOK НЕ УДАЛОСЬ для org %s: %s",
                        organization_id,
                        exc,
                    )
