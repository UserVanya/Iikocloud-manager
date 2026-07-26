"""Webhooks core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CorrelationIdResponse,
    GetWebHookSettingsRequest,
    GetWebHookSettingsResponse,
    UpdateWebHookSettingsRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class WebhooksCoreMixin(_ManagerBase):
    """Core-методы Webhooks API."""

    async def get_webhook_settings(
        self,
        request: GetWebHookSettingsRequest,
    ) -> GetWebHookSettingsResponse:
        """Получить webhook-настройки организации.

        Ответ содержит auth_token — чувствительные данные, не логировать.

        Args:
            request: Параметры запроса (organization_id)

        Returns:
            Ответ с webhook-настройками (web_hooks_uri, auth_token)
        """

        async def api_call() -> GetWebHookSettingsResponse:
            api = await self.get_webhooks_api()
            return await api.get_webhook_settings(
                get_web_hook_settings_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_WEBHOOK_SETTINGS, api_call
        )

    async def update_webhook_settings(
        self,
        request: UpdateWebHookSettingsRequest,
    ) -> CorrelationIdResponse:
        """Обновить webhook-настройки организации.

        Перезаписывает webhook-конфиг api-логина (web_hooks_uri, auth_token).

        Args:
            request: Параметры запроса (organization_id, web_hooks_uri, ...)

        Returns:
            CorrelationIdResponse с correlation_id операции
        """

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_webhooks_api()
            return await api.update_webhook_settings(
                update_web_hook_settings_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_WEBHOOK_SETTINGS, api_call
        )
