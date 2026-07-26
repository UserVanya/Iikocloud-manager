"""Messages core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CheckSmsStatusRequest,
    CheckSmsStatusResponse,
    SendEmailRequest,
    SendSmsRequest,
    SendSmsResponse,
    SmsSendingPossibilityRequest,
    SmsSendingPossibilityResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class MessagesCoreMixin(_ManagerBase):
    """Core-методы Messages API (SMS/email рассылки лояльности)."""

    async def check_sms_sending_possibility(
        self,
        request: SmsSendingPossibilityRequest,
    ) -> SmsSendingPossibilityResponse:
        """Проверить возможность отправки SMS для организации.

        Args:
            request: Параметры запроса SmsSendingPossibilityRequest

        Returns:
            Ответ с признаком возможности отправки SMS
        """

        async def api_call() -> SmsSendingPossibilityResponse:
            api = await self.get_messages_api()
            return await api.check_sms_sending_possibility(
                sms_sending_possibility_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHECK_SMS_SENDING_POSSIBILITY, api_call
        )

    async def check_sms_status(
        self,
        request: CheckSmsStatusRequest,
    ) -> CheckSmsStatusResponse:
        """Получить статусы отправленных SMS по их идентификаторам.

        Args:
            request: Параметры запроса CheckSmsStatusRequest

        Returns:
            Ответ со статусами SMS
        """

        async def api_call() -> CheckSmsStatusResponse:
            api = await self.get_messages_api()
            return await api.check_sms_status(check_sms_status_request=request)

        return await self.execute_with_retry(
            ApiMethod.CHECK_SMS_STATUS, api_call
        )

    async def send_loyalty_sms(
        self,
        request: SendSmsRequest,
    ) -> SendSmsResponse:
        """Отправить SMS клиенту от имени организации.

        Операция требует restriction group ``Loyalty: messages``.

        Args:
            request: Параметры запроса SendSmsRequest

        Returns:
            Ответ с идентификатором отправленного SMS
        """

        async def api_call() -> SendSmsResponse:
            api = await self.get_messages_api()
            return await api.send_loyalty_sms(send_sms_request=request)

        return await self.execute_with_retry(
            ApiMethod.SEND_LOYALTY_SMS, api_call
        )

    async def send_loyalty_email(
        self,
        request: SendEmailRequest,
    ) -> None:
        """Отправить email клиенту от имени организации (object-ответ -> None).

        Операция требует restriction group ``Loyalty: messages``.

        Args:
            request: Параметры запроса SendEmailRequest
        """

        async def api_call() -> None:
            api = await self.get_messages_api()
            await api.send_loyalty_email(send_email_request=request)

        return await self.execute_with_retry(
            ApiMethod.SEND_LOYALTY_EMAIL, api_call
        )
