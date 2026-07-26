"""Discounts helpers mixin — convenience-методы расчёта лояльности."""

from uuid import UUID

from iikocloud_client import (
    CalculateCheckinRequest,
    CalculateCheckinResponse,
    DeliveryOrderCreateCustomer,
    DeliveryOrderCreateItem,
    DeliveryOrderCreateLoyaltyInfo,
    DeliveryOrderCreatePayload,
    DeliveryOrderCreateServiceType,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.discounts.core import DiscountsCoreMixin


class DiscountsHelpersMixin(DiscountsCoreMixin):
    """Публичный discounts mixin с convenience-методами."""

    async def calculate_order_loyalty(
        self,
        organization_id: str | UUID,
        items: list[DeliveryOrderCreateItem],
        phone: str,
        *,
        coupon: str | None = None,
        customer: DeliveryOrderCreateCustomer | None = None,
        applicable_manual_conditions: list[UUID] | None = None,
        order_service_type: str | None = None,
        terminal_group_id: str | UUID | None = None,
    ) -> CalculateCheckinResponse:
        """Расчёт скидок/лояльности заказа (короткая форма calculate).

        items собираются через build_product_item / build_compound_item.
        Купон и ручные условия передаются через order.loyalty_info
        (верхнеуровневые поля request — obsolete).
        """
        loyalty_info = None
        if coupon is not None or applicable_manual_conditions is not None:
            loyalty_info = DeliveryOrderCreateLoyaltyInfo(
                coupon=coupon,
                applicable_manual_conditions=applicable_manual_conditions,
            )
        order = DeliveryOrderCreatePayload(
            phone=phone,
            items=items,
            loyalty_info=loyalty_info,
            customer=customer,
            order_service_type=(
                DeliveryOrderCreateServiceType(order_service_type)
                if order_service_type
                else None
            ),
        )
        return await self.calculate_loyalty_checkin(
            CalculateCheckinRequest(
                organization_id=as_uuid(organization_id),
                order=order,
                terminal_group_id=(
                    as_uuid(terminal_group_id) if terminal_group_id else None
                ),
            )
        )
