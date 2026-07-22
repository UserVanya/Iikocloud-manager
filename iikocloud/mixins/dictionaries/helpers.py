"""Dictionaries helpers mixin — convenience-методы через core."""

from uuid import UUID

from iikocloud_client import (
    CancelCausesRequest,
    CancelCausesResponse,
    DiscountsRequest,
    DiscountsResponse,
    OrderTypesRequest,
    OrderTypesResponse,
    PaymentTypesRequest,
    PaymentTypesResponse,
    RemovalTypesRequest,
    RemovalTypesResponse,
)

from iikocloud.mixins.dictionaries.core import DictionariesCoreMixin


def _as_uuid(value: str | UUID) -> UUID:
    """Привести organization_id к UUID."""
    if isinstance(value, UUID):
        return value
    return UUID(value)


class DictionariesHelpersMixin(DictionariesCoreMixin):
    """Публичный dictionaries mixin с convenience-методами."""

    async def get_cancel_causes_by_organization(
        self,
        organization_id: str | UUID,
    ) -> CancelCausesResponse:
        """Получить причины отмены для организации.

        Args:
            organization_id: ID организации (str или UUID)

        Returns:
            Ответ со списком причин отмены организации
        """
        request = CancelCausesRequest(
            organization_ids=[_as_uuid(organization_id)],
        )
        return await self.get_cancel_causes(request)

    async def get_delivery_order_types_by_organization(
        self,
        organization_id: str | UUID,
    ) -> OrderTypesResponse:
        """Получить типы заказов доставки для организации.

        Args:
            organization_id: ID организации (str или UUID)

        Returns:
            Ответ со списком типов заказов организации
        """
        request = OrderTypesRequest(
            organization_ids=[_as_uuid(organization_id)],
        )
        return await self.get_delivery_order_types(request)

    async def get_payment_types_by_organization(
        self,
        organization_id: str | UUID,
    ) -> PaymentTypesResponse:
        """Получить типы оплаты для организации.

        Args:
            organization_id: ID организации (str или UUID)

        Returns:
            Ответ со списком типов оплаты организации
        """
        request = PaymentTypesRequest(
            organization_ids=[_as_uuid(organization_id)],
        )
        return await self.get_payment_types(request)

    async def get_discounts_by_organization(
        self,
        organization_id: str | UUID,
    ) -> DiscountsResponse:
        """Получить скидки для организации.

        Args:
            organization_id: ID организации (str или UUID)

        Returns:
            Ответ со списком скидок организации
        """
        request = DiscountsRequest(
            organization_ids=[_as_uuid(organization_id)],
        )
        return await self.get_discounts(request)

    async def get_removal_types_by_organization(
        self,
        organization_id: str | UUID,
    ) -> RemovalTypesResponse:
        """Получить типы списания для организации.

        Args:
            organization_id: ID организации (str или UUID)

        Returns:
            Ответ со списком типов списания организации
        """
        request = RemovalTypesRequest(
            organization_ids=[_as_uuid(organization_id)],
        )
        return await self.get_removal_types(request)
