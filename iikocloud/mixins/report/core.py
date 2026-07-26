"""Report core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    GetTransactionsReportByPeriodRequest,
    GetTransactionsReportByPeriodResponse,
    GetTransactionsReportByRevisionRequest,
    GetTransactionsReportByRevisionResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class ReportCoreMixin(_ManagerBase):
    """Core-методы Report API."""

    async def get_customer_transactions_by_date(
        self,
        request: GetTransactionsReportByPeriodRequest,
    ) -> GetTransactionsReportByPeriodResponse:
        """Получить транзакции клиента за период (постранично).

        Даты трактуются как UTC включительно (date_from..date_to).

        Args:
            request: Параметры запроса (customer/organization, период, пагинация)

        Returns:
            Ответ со списком транзакций за период
        """

        async def api_call() -> GetTransactionsReportByPeriodResponse:
            api = await self.get_report_api()
            return await api.get_customer_transactions_by_date(
                get_transactions_report_by_period_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_CUSTOMER_TRANSACTIONS_BY_DATE, api_call
        )

    async def get_customer_transactions_by_revision(
        self,
        request: GetTransactionsReportByRevisionRequest,
    ) -> GetTransactionsReportByRevisionResponse:
        """Получить транзакции клиента инкрементально по ревизии.

        Ответ несёт last_revision/last_transaction_id для следующего запроса.

        Args:
            request: Параметры запроса (customer/organization, ревизия, page_size)

        Returns:
            Ответ со списком транзакций и маркерами продолжения
        """

        async def api_call() -> GetTransactionsReportByRevisionResponse:
            api = await self.get_report_api()
            return await api.get_customer_transactions_by_revision(
                get_transactions_report_by_revision_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_CUSTOMER_TRANSACTIONS_BY_REVISION, api_call
        )
