"""Customers helpers mixin — convenience-методы через core."""

from uuid import UUID

from iikocloud_client import (
    GetCustomerInfoByPhoneRequest,
    GetCustomerInfoResponse,
)

from iikocloud.mixins.customers.core import CustomersCoreMixin


def _as_uuid(value: str | UUID) -> UUID:
    """Привести organization_id к UUID."""
    if isinstance(value, UUID):
        return value
    return UUID(value)


class CustomersHelpersMixin(CustomersCoreMixin):
    """Публичный customers mixin с convenience-методами."""

    async def get_customer_by_phone(
        self,
        organization_id: str | UUID,
        phone: str,
    ) -> GetCustomerInfoResponse:
        """Получить клиента по номеру телефона.

        Args:
            organization_id: ID организации (str или UUID)
            phone: Номер телефона клиента

        Returns:
            Ответ с информацией о клиенте
        """
        request = GetCustomerInfoByPhoneRequest(
            organization_id=_as_uuid(organization_id),
            type="phone",
            phone=phone,
        )
        return await self.get_customer_info(request)
