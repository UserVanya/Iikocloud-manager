"""DeliveriesRetrieve helpers mixin — короткие формы чтения заказов."""

from datetime import datetime, timedelta
from uuid import UUID

from iikocloud_client import (
    OrderInfo,
    OrdersByDeliveryDateAndPhoneRequest,
    OrdersByIdRequest,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.deliveries_retrieve.core import (
    DeliveriesRetrieveCoreMixin,
)

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.000"


class DeliveriesRetrieveHelpersMixin(DeliveriesRetrieveCoreMixin):
    """Публичный deliveries-retrieve mixin с convenience-методами."""

    async def get_delivery_by_id(
        self,
        organization_id: str | UUID,
        order_id: str | UUID,
    ) -> OrderInfo | None:
        """Один заказ по id (None, если не найден)."""
        response = await self.get_deliveries_by_id(
            OrdersByIdRequest(
                organization_id=as_uuid(organization_id),
                order_ids=[as_uuid(order_id)],
            )
        )
        orders = response.orders or []
        return orders[0] if orders else None

    async def get_customer_deliveries(
        self,
        organization_ids: list[str | UUID],
        phone: str,
        days: int = 7,
    ) -> list[OrderInfo]:
        """Заказы клиента по телефону за последние N дней (плоский список).

        Даты — локальное время терминала (гарантия доступности — 7 дней).
        """
        date_to = datetime.now()
        date_from = date_to - timedelta(days=days)
        response = await self.get_deliveries_by_delivery_date_and_phone(
            OrdersByDeliveryDateAndPhoneRequest(
                organization_ids=[as_uuid(oid) for oid in organization_ids],
                phone=phone,
                delivery_date_from=date_from.strftime(_DATE_FORMAT),
                delivery_date_to=date_to.strftime(_DATE_FORMAT),
            )
        )
        return [
            order
            for org_orders in response.orders_by_organizations or []
            for order in org_orders.orders or []
        ]
