"""Deliveries helpers mixin — конструкторы позиций и короткие формы."""

from uuid import UUID

from iikocloud_client import (
    CancelOrderRequest,
    CorrelationIdResponse,
    DeliveryOrderCreateCompoundItem,
    DeliveryOrderCreateCompoundItemComponent,
    DeliveryOrderCreateProductItem,
    Modifier,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.deliveries.core import DeliveriesCoreMixin


class DeliveriesHelpersMixin(DeliveriesCoreMixin):
    """Публичный deliveries mixin с convenience-методами."""

    @staticmethod
    def build_product_item(
        product_id: str | UUID,
        price: float,
        amount: float = 1.0,
        *,
        product_size_id: str | UUID | None = None,
        comment: str | None = None,
        modifiers: list[Modifier] | None = None,
    ) -> DeliveryOrderCreateProductItem:
        """Собрать позицию-товар (дискриминатор type="Product").

        Args:
            product_id: ID продукта из номенклатуры
            price: Цена за единицу (обязательна в API)
            amount: Количество
            product_size_id: ID размера (для размерных товаров)
            comment: Комментарий к позиции
            modifiers: Модификаторы позиции
        """
        return DeliveryOrderCreateProductItem(
            type="Product",
            product_id=as_uuid(product_id),
            price=price,
            amount=amount,
            product_size_id=as_uuid(product_size_id) if product_size_id else None,
            comment=comment,
            modifiers=modifiers,
        )

    @staticmethod
    def build_compound_item(
        primary_product_id: str | UUID,
        *,
        secondary_product_id: str | UUID | None = None,
        amount: float = 1.0,
        primary_price: float | None = None,
        secondary_price: float | None = None,
        common_modifiers: list[Modifier] | None = None,
        comment: str | None = None,
    ) -> DeliveryOrderCreateCompoundItem:
        """Собрать составную позицию (дискриминатор type="Compound").

        Цена в API задаётся на уровне компонента (optional).
        """
        primary = DeliveryOrderCreateCompoundItemComponent(
            product_id=as_uuid(primary_product_id),
            price=primary_price,
        )
        secondary = (
            DeliveryOrderCreateCompoundItemComponent(
                product_id=as_uuid(secondary_product_id),
                price=secondary_price,
            )
            if secondary_product_id
            else None
        )
        return DeliveryOrderCreateCompoundItem(
            type="Compound",
            amount=amount,
            primary_component=primary,
            secondary_component=secondary,
            common_modifiers=common_modifiers,
            comment=comment,
        )

    async def cancel_order(
        self,
        organization_id: str | UUID,
        order_id: str | UUID,
        cancel_comment: str | None = None,
    ) -> CorrelationIdResponse:
        """Отменить заказ (короткая форма cancel_delivery_order)."""
        return await self.cancel_delivery_order(
            CancelOrderRequest(
                organization_id=as_uuid(organization_id),
                order_id=as_uuid(order_id),
                cancel_comment=cancel_comment,
            )
        )
