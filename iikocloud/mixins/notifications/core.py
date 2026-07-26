"""Notifications core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CorrelationIdResponse,
    SendNotificationRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class NotificationsCoreMixin(_ManagerBase):
    """Core-методы Notifications API (уведомления сотрудникам/клиентам)."""

    async def send_notification(
        self,
        request: SendNotificationRequest,
    ) -> CorrelationIdResponse:
        """Отправить уведомление.

        Args:
            request: Полиморфный запрос SendNotificationRequest; сейчас
                поддержан подкласс order_attention

        Returns:
            Ответ с correlationId
        """

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_notifications_api()
            return await api.send_notification(send_notification_request=request)

        return await self.execute_with_retry(
            ApiMethod.SEND_NOTIFICATION, api_call
        )
