"""Invoice Processing references core mixins — обёртки SDK."""

from iikocloud_client import (
    AccountTransactionsListRequest,
    AccountTransactionsResponse,
    DocumentTransactionItem,
    DocumentTransactionsListRequest,
    GetCounteragentsRequest,
    GetCounteragentsResponse,
    NomenclatureProductUpdateBarcodesRequest,
    NomenclatureProductUpdateBarcodesResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class AccountTransactionsCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: проводки по счету."""

    async def list_finance_account_transactions(
        self, request: AccountTransactionsListRequest
    ) -> AccountTransactionsResponse:
        """Проводки по счету за период."""

        async def api_call() -> AccountTransactionsResponse:
            api = await self.get_account_transactions_api()
            return await api.list_finance_account_transactions(
                account_transactions_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_FINANCE_ACCOUNT_TRANSACTIONS, api_call
        )


class DocumentTransactionsCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: проводки по документу."""

    async def list_finance_document_transactions(
        self, request: DocumentTransactionsListRequest
    ) -> list[DocumentTransactionItem]:
        """Проводки по документу."""

        async def api_call() -> list[DocumentTransactionItem]:
            api = await self.get_document_transactions_api()
            return await api.list_finance_document_transactions(
                document_transactions_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_FINANCE_DOCUMENT_TRANSACTIONS, api_call
        )


class CounteragentsCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: контрагенты."""

    async def list_inventory_counteragents(
        self, request: GetCounteragentsRequest
    ) -> GetCounteragentsResponse:
        """Список контрагентов."""

        async def api_call() -> GetCounteragentsResponse:
            api = await self.get_counteragents_api()
            return await api.list_inventory_counteragents(
                get_counteragents_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_INVENTORY_COUNTERAGENTS, api_call
        )


class InvoiceNomenclatureCoreMixin(_ManagerBase):
    """Core-методы Invoice Processing: номенклатура (штрихкоды)."""

    async def update_nomenclature_product_barcodes(
        self, request: NomenclatureProductUpdateBarcodesRequest
    ) -> NomenclatureProductUpdateBarcodesResponse:
        """Обновить штрихкоды товара."""

        async def api_call() -> NomenclatureProductUpdateBarcodesResponse:
            api = await self.get_nomenclature_product_api()
            return await api.update_nomenclature_product_barcodes(
                nomenclature_product_update_barcodes_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_NOMENCLATURE_PRODUCT_BARCODES, api_call
        )
