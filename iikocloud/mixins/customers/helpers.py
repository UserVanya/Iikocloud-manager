"""Customers helpers mixin — convenience-методы через core."""

from uuid import UUID

from iikocloud_client import (
    GetCustomerInfoByCardNumberRequest,
    GetCustomerInfoByCardTrackRequest,
    GetCustomerInfoByEmailRequest,
    GetCustomerInfoByIdRequest,
    GetCustomerInfoByPhoneRequest,
    GetCustomerInfoResponse,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.customers.core import CustomersCoreMixin


class CustomersHelpersMixin(CustomersCoreMixin):
    """Публичный customers mixin с convenience-методами lookup.

    SDK ``get_customer_info`` принимает discriminator ``type``:
    ``phone`` | ``id`` | ``email`` | ``cardNumber`` | ``cardTrack``.
    """

    async def get_customer_by_phone(
        self,
        organization_id: str | UUID,
        phone: str,
    ) -> GetCustomerInfoResponse:
        """Получить клиента по номеру телефона."""
        request = GetCustomerInfoByPhoneRequest(
            organization_id=as_uuid(organization_id),
            type="phone",
            phone=phone,
        )
        return await self.get_customer_info(request)

    async def get_customer_by_id(
        self,
        organization_id: str | UUID,
        customer_id: str | UUID,
    ) -> GetCustomerInfoResponse:
        """Получить клиента по ID (loyalty customer id)."""
        request = GetCustomerInfoByIdRequest(
            organization_id=as_uuid(organization_id),
            type="id",
            id=str(customer_id),
        )
        return await self.get_customer_info(request)

    async def get_customer_by_email(
        self,
        organization_id: str | UUID,
        email: str,
    ) -> GetCustomerInfoResponse:
        """Получить клиента по email."""
        request = GetCustomerInfoByEmailRequest(
            organization_id=as_uuid(organization_id),
            type="email",
            email=email,
        )
        return await self.get_customer_info(request)

    async def get_customer_by_card_number(
        self,
        organization_id: str | UUID,
        card_number: str,
    ) -> GetCustomerInfoResponse:
        """Получить клиента по номеру карты лояльности."""
        request = GetCustomerInfoByCardNumberRequest(
            organization_id=as_uuid(organization_id),
            type="cardNumber",
            card_number=card_number,
        )
        return await self.get_customer_info(request)

    async def get_customer_by_card_track(
        self,
        organization_id: str | UUID,
        card_track: str,
    ) -> GetCustomerInfoResponse:
        """Получить клиента по магнитной дорожке карты."""
        request = GetCustomerInfoByCardTrackRequest(
            organization_id=as_uuid(organization_id),
            type="cardTrack",
            card_track=card_track,
        )
        return await self.get_customer_info(request)
