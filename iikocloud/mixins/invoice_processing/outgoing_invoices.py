"""Invoice Processing outgoing invoices core mixin — обёртки SDK."""

from iikocloud_client import (
    AccountingTransactionUserResponse,
    GetByIDRequest,
    GetCostPricesRequest,
    GetCostPricesResponse,
    ListRequest,
    OutgoingInvoice,
    OutgoingInvoiceRequest,
    OutgoingInvoiceSaveResponse,
    PayOutgoingInvoiceRequest,
    SetPaymentDateOutgoingRequest,
    SetPaymentDateOutgoingResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class OutgoingInvoicesCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: расходные накладные (outgoing invoices)."""

    async def create_inventory_outgoing_invoice(
        self, request: OutgoingInvoiceRequest
    ) -> OutgoingInvoiceSaveResponse:
        """Создать расходную накладную."""

        async def api_call() -> OutgoingInvoiceSaveResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.create_inventory_outgoing_invoice(
                outgoing_invoice_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_INVENTORY_OUTGOING_INVOICE, api_call
        )

    async def update_inventory_outgoing_invoice(
        self, request: OutgoingInvoiceRequest
    ) -> OutgoingInvoiceSaveResponse:
        """Обновить расходную накладную."""

        async def api_call() -> OutgoingInvoiceSaveResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.update_inventory_outgoing_invoice(
                outgoing_invoice_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_INVENTORY_OUTGOING_INVOICE, api_call
        )

    async def get_inventory_outgoing_invoice(
        self, request: GetByIDRequest
    ) -> OutgoingInvoice:
        """Расходная накладная по id."""

        async def api_call() -> OutgoingInvoice:
            api = await self.get_outgoing_invoices_api()
            return await api.get_inventory_outgoing_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_INVENTORY_OUTGOING_INVOICE, api_call
        )

    async def list_inventory_outgoing_invoices(
        self, request: ListRequest
    ) -> list[OutgoingInvoice]:
        """Список расходных накладных за период."""

        async def api_call() -> list[OutgoingInvoice]:
            api = await self.get_outgoing_invoices_api()
            return await api.list_inventory_outgoing_invoices(list_request=request)

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_OUTGOING_INVOICES, api_call
        )

    async def post_inventory_outgoing_invoice(
        self, request: GetByIDRequest
    ) -> OutgoingInvoiceSaveResponse:
        """Провести расходную накладную."""

        async def api_call() -> OutgoingInvoiceSaveResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.post_inventory_outgoing_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.POST_INVENTORY_OUTGOING_INVOICE, api_call
        )

    async def unpost_inventory_outgoing_invoice(
        self, request: GetByIDRequest
    ) -> OutgoingInvoiceSaveResponse:
        """Отменить проведение расходной накладной."""

        async def api_call() -> OutgoingInvoiceSaveResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.unpost_inventory_outgoing_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNPOST_INVENTORY_OUTGOING_INVOICE, api_call
        )

    async def cancel_inventory_outgoing_invoice(
        self, request: GetByIDRequest
    ) -> OutgoingInvoiceSaveResponse:
        """Отменить (удалить) расходную накладную."""

        async def api_call() -> OutgoingInvoiceSaveResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.cancel_inventory_outgoing_invoice(
                get_by_id_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_INVENTORY_OUTGOING_INVOICE, api_call
        )

    async def add_inventory_outgoing_invoice_payment(
        self, request: PayOutgoingInvoiceRequest
    ) -> AccountingTransactionUserResponse:
        """Добавить оплату по расходной накладной."""

        async def api_call() -> AccountingTransactionUserResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.add_inventory_outgoing_invoice_payment(
                pay_outgoing_invoice_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_INVENTORY_OUTGOING_INVOICE_PAYMENT, api_call
        )

    async def set_inventory_outgoing_invoice_payment_date(
        self, request: SetPaymentDateOutgoingRequest
    ) -> SetPaymentDateOutgoingResponse:
        """Установить дату оплаты расходной накладной."""

        async def api_call() -> SetPaymentDateOutgoingResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.set_inventory_outgoing_invoice_payment_date(
                set_payment_date_outgoing_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.SET_INVENTORY_OUTGOING_INVOICE_PAYMENT_DATE, api_call
        )

    async def calculate_inventory_cost_prices(
        self, request: GetCostPricesRequest
    ) -> GetCostPricesResponse:
        """Рассчитать себестоимость товаров на складах."""

        async def api_call() -> GetCostPricesResponse:
            api = await self.get_outgoing_invoices_api()
            return await api.calculate_inventory_cost_prices(
                get_cost_prices_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CALCULATE_INVENTORY_COST_PRICES, api_call
        )
