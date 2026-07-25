"""Deliveries core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    AddOrderItemsRequest,
    AddOrderPaymentsRequest,
    CancelDeliveryConfirmationRequest,
    CancelOrderRequest,
    ChangeCompleteBeforeRequest,
    ChangeDeliveryCommentRequest,
    ChangeDeliveryOperatorRequest,
    ChangeDeliveryPointRequest,
    ChangeDriverInfoRequest,
    ChangeExternalDataRequest,
    ChangePaymentsRequest,
    ChangeServiceTypeRequest,
    CloseDeliveryOrderRequest,
    ConfirmDeliveryRequest,
    CorrelationIdResponse,
    CreateOrderRequest,
    OrderResponse,
    PrintBillRequest,
    PrintDeliveryBillRequest,
    UpdateDeliveryStatusRequest,
    UpdateOrderProblemRequest,
    UpdateTrackingLinkRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DeliveriesCoreMixin(_ManagerBase):
    """Core-методы Deliveries create & update API.

    Все методы, кроме create_delivery_order и update_delivery_tracking_link,
    — асинхронные команды: ответ CorrelationIdResponse, статус исполнения
    опрашивается через /api/1/commands/status.
    """

    async def create_delivery_order(
        self,
        request: CreateOrderRequest,
    ) -> OrderResponse:
        """Создать заказ доставки.

        Returns:
            OrderResponse с order_info.creation_status
            (Success / InProgress / Error)
        """

        async def api_call() -> OrderResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.create_delivery_order(create_order_request=request)

        return await self.execute_with_retry(
            ApiMethod.CREATE_DELIVERY_ORDER, api_call
        )

    async def add_delivery_order_items(
        self,
        request: AddOrderItemsRequest,
    ) -> CorrelationIdResponse:
        """Добавить позиции в заказ (iiko >= 7.4.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.add_delivery_order_items(
                add_order_items_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_DELIVERY_ORDER_ITEMS, api_call
        )

    async def add_delivery_order_payments(
        self,
        request: AddOrderPaymentsRequest,
    ) -> CorrelationIdResponse:
        """Добавить оплаты в заказ (iiko >= 8.4.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.add_delivery_order_payments(
                add_order_payments_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_DELIVERY_ORDER_PAYMENTS, api_call
        )

    async def cancel_delivery_order(
        self,
        request: CancelOrderRequest,
    ) -> CorrelationIdResponse:
        """Отменить заказ (статус Cancelled; заказ не удаляется физически)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.cancel_delivery_order(cancel_order_request=request)

        return await self.execute_with_retry(
            ApiMethod.CANCEL_DELIVERY_ORDER, api_call
        )

    async def cancel_delivery_confirmation(
        self,
        request: CancelDeliveryConfirmationRequest,
    ) -> CorrelationIdResponse:
        """Отменить подтверждение заказа (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.cancel_delivery_confirmation(
                cancel_delivery_confirmation_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_DELIVERY_CONFIRMATION, api_call
        )

    async def confirm_delivery(
        self,
        request: ConfirmDeliveryRequest,
    ) -> CorrelationIdResponse:
        """Подтвердить заказ (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.confirm_delivery(confirm_delivery_request=request)

        return await self.execute_with_retry(
            ApiMethod.CONFIRM_DELIVERY, api_call
        )

    async def change_delivery_comment(
        self,
        request: ChangeDeliveryCommentRequest,
    ) -> CorrelationIdResponse:
        """Изменить комментарий заказа."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_comment(
                change_delivery_comment_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_COMMENT, api_call
        )

    async def change_delivery_complete_before(
        self,
        request: ChangeCompleteBeforeRequest,
    ) -> CorrelationIdResponse:
        """Изменить время, к которому заказ должен быть готов."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_complete_before(
                change_complete_before_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_COMPLETE_BEFORE, api_call
        )

    async def change_delivery_driver_info(
        self,
        request: ChangeDriverInfoRequest,
    ) -> CorrelationIdResponse:
        """Изменить водителя/время доставки (iiko >= 8.6.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_driver_info(
                change_driver_info_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_DRIVER_INFO, api_call
        )

    async def change_delivery_external_data(
        self,
        request: ChangeExternalDataRequest,
    ) -> CorrelationIdResponse:
        """Изменить external data заказа."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_external_data(
                change_external_data_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_EXTERNAL_DATA, api_call
        )

    async def change_delivery_operator(
        self,
        request: ChangeDeliveryOperatorRequest,
    ) -> CorrelationIdResponse:
        """Изменить оператора заказа (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_operator(
                change_delivery_operator_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_OPERATOR, api_call
        )

    async def change_delivery_payments(
        self,
        request: ChangePaymentsRequest,
    ) -> CorrelationIdResponse:
        """Заменить все оплаты заказа (падает при processed payments)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_payments(
                change_payments_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_PAYMENTS, api_call
        )

    async def change_delivery_point(
        self,
        request: ChangeDeliveryPointRequest,
    ) -> CorrelationIdResponse:
        """Изменить точку доставки (адрес/координаты)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_point(
                change_delivery_point_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_POINT, api_call
        )

    async def change_delivery_service_type(
        self,
        request: ChangeServiceTypeRequest,
    ) -> CorrelationIdResponse:
        """Изменить тип сервиса (DeliveryByCourier / DeliveryByClient)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.change_delivery_service_type(
                change_service_type_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CHANGE_DELIVERY_SERVICE_TYPE, api_call
        )

    async def close_delivery_order(
        self,
        request: CloseDeliveryOrderRequest,
    ) -> CorrelationIdResponse:
        """Закрыть заказ (iiko >= 7.4.6; courier — только OnWay/Delivered с 8.0.6)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.close_delivery_order(
                close_delivery_order_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CLOSE_DELIVERY_ORDER, api_call
        )

    async def print_delivery_bill(
        self,
        request: PrintDeliveryBillRequest,
    ) -> CorrelationIdResponse:
        """Печать чека доставки (iiko >= 7.6.1)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.print_delivery_bill(
                print_delivery_bill_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.PRINT_DELIVERY_BILL, api_call
        )

    async def print_table_order_bill(
        self,
        request: PrintBillRequest,
    ) -> CorrelationIdResponse:
        """Печать чека столового заказа (endpoint /api/1/order/print_bill)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.print_table_order_bill(print_bill_request=request)

        return await self.execute_with_retry(
            ApiMethod.PRINT_TABLE_ORDER_BILL, api_call
        )

    async def update_delivery_order_problem(
        self,
        request: UpdateOrderProblemRequest,
    ) -> CorrelationIdResponse:
        """Установить/снять флаг проблемы заказа."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.update_delivery_order_problem(
                update_order_problem_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_DELIVERY_ORDER_PROBLEM, api_call
        )

    async def update_delivery_order_status(
        self,
        request: UpdateDeliveryStatusRequest,
    ) -> CorrelationIdResponse:
        """Изменить статус доставки (Waiting / OnWay / Delivered)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_deliveries_create_and_update_api()
            return await api.update_delivery_order_status(
                update_delivery_status_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_DELIVERY_ORDER_STATUS, api_call
        )

    async def update_delivery_tracking_link(
        self,
        request: UpdateTrackingLinkRequest,
    ) -> None:
        """Обновить tracking-ссылку заказа (ответ без тела)."""

        async def api_call() -> None:
            api = await self.get_deliveries_create_and_update_api()
            await api.update_delivery_tracking_link(
                update_tracking_link_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_DELIVERY_TRACKING_LINK, api_call
        )
