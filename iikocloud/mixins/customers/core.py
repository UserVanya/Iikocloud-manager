"""Customers core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    AddCustomerToProgramRequest,
    AddCustomerToProgramResponse,
    AddMagnetCardRequest,
    CancelHoldMoneyRequest,
    ChangeUserBalanceRequest,
    CreateOrUpdateCustomerRequest,
    CreateOrUpdateCustomerResponse,
    DeleteCustomersRequest,
    DeleteCustomersResponse,
    DeleteMagnetCardRequest,
    GetCountersRequest,
    GetCountersResponse,
    GetCustomerInfoRequest,
    GetCustomerInfoResponse,
    HoldMoneyRequest,
    HoldMoneyResponse,
    RestoreCustomersRequest,
    RestoreCustomersResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class CustomersCoreMixin(_ManagerBase):
    """Core-методы Customers API."""

    async def add_customer_magnet_card(
        self,
        request: AddMagnetCardRequest,
    ) -> None:
        """Привязать магнитную карту к клиенту.

        Args:
            request: cardNumber, cardTrack, customerId, organizationId
        """

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.add_customer_magnet_card(add_magnet_card_request=request)

        return await self.execute_with_retry(
            ApiMethod.ADD_CUSTOMER_MAGNET_CARD, api_call
        )

    async def remove_customer_magnet_card(
        self,
        request: DeleteMagnetCardRequest,
    ) -> None:
        """Отвязать магнитную карту от клиента.

        Args:
            request: cardTrack, customerId, organizationId
        """

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.remove_customer_magnet_card(
                delete_magnet_card_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.REMOVE_CUSTOMER_MAGNET_CARD, api_call
        )

    async def add_customer_to_program(
        self,
        request: AddCustomerToProgramRequest,
    ) -> AddCustomerToProgramResponse:
        """Добавить клиента в программу лояльности.

        Args:
            request: customerId, organizationId, programId

        Returns:
            Ответ с userWalletId/walletId кошелька программы
        """

        async def api_call() -> AddCustomerToProgramResponse:
            api = await self.get_customers_api()
            return await api.add_customer_to_program(
                add_customer_to_program_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_CUSTOMER_TO_PROGRAM, api_call
        )

    async def create_or_update_customer(
        self,
        request: CreateOrUpdateCustomerRequest,
    ) -> CreateOrUpdateCustomerResponse:
        """Создать или обновить клиента.

        Args:
            request: Параметры запроса CreateOrUpdateCustomerRequest

        Returns:
            Ответ с данными созданного/обновлённого клиента
        """

        async def api_call() -> CreateOrUpdateCustomerResponse:
            api = await self.get_customers_api()
            return await api.create_or_update_customer(
                create_or_update_customer_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_OR_UPDATE_CUSTOMER, api_call
        )

    async def get_customer_info(
        self,
        request: GetCustomerInfoRequest,
    ) -> GetCustomerInfoResponse:
        """Получить информацию о клиенте.

        Args:
            request: Параметры запроса (phone, id, email, card и т.д.)

        Returns:
            Ответ с информацией о клиенте
        """

        async def api_call() -> GetCustomerInfoResponse:
            api = await self.get_customers_api()
            return await api.get_customer_info(
                get_customer_info_request=request
            )

        return await self.execute_with_retry(ApiMethod.GET_CUSTOMER_INFO, api_call)

    async def delete_customers(
        self,
        request: DeleteCustomersRequest,
    ) -> DeleteCustomersResponse:
        """Удалить клиентов.

        Args:
            request: Параметры запроса DeleteCustomersRequest

        Returns:
            Ответ об удалении клиентов
        """

        async def api_call() -> DeleteCustomersResponse:
            api = await self.get_customers_api()
            return await api.delete_customers(
                delete_customers_request=request
            )

        return await self.execute_with_retry(ApiMethod.DELETE_CUSTOMERS, api_call)

    async def restore_customers(
        self,
        request: RestoreCustomersRequest,
    ) -> RestoreCustomersResponse:
        """Восстановить удалённых клиентов.

        Args:
            request: Параметры запроса RestoreCustomersRequest

        Returns:
            Ответ о восстановлении клиентов
        """

        async def api_call() -> RestoreCustomersResponse:
            api = await self.get_customers_api()
            return await api.restore_customers(
                restore_customers_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.RESTORE_CUSTOMERS, api_call
        )

    @staticmethod
    def _require_balance_fields(request: ChangeUserBalanceRequest) -> None:
        """customerId/walletId в SDK optional, но семантически обязательны."""
        if request.customer_id is None or request.wallet_id is None:
            raise ValueError(
                "customer_id и wallet_id обязательны для операций с балансом"
            )

    async def hold_customer_balance(
        self,
        request: HoldMoneyRequest,
    ) -> HoldMoneyResponse:
        """Захолдировать средства на кошельке клиента.

        Идемпотентность — через request.transaction_id
        (если не задан, сервер сгенерирует и вернёт в ответе).
        """

        async def api_call() -> HoldMoneyResponse:
            api = await self.get_customers_api()
            return await api.hold_customer_balance(hold_money_request=request)

        return await self.execute_with_retry(
            ApiMethod.HOLD_CUSTOMER_BALANCE, api_call
        )

    async def cancel_customer_balance_hold(
        self,
        request: CancelHoldMoneyRequest,
    ) -> None:
        """Отменить холд по transactionId."""

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.cancel_customer_balance_hold(
                cancel_hold_money_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CANCEL_CUSTOMER_BALANCE_HOLD, api_call
        )

    async def top_up_customer_balance(
        self,
        request: ChangeUserBalanceRequest,
    ) -> None:
        """Пополнить кошелёк клиента (sum строго положительная)."""

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.top_up_customer_balance(
                change_user_balance_request=request
            )

        self._require_balance_fields(request)
        return await self.execute_with_retry(
            ApiMethod.TOP_UP_CUSTOMER_BALANCE, api_call
        )

    async def withdraw_customer_balance(
        self,
        request: ChangeUserBalanceRequest,
    ) -> None:
        """Списать средства с кошелька клиента (sum строго положительная)."""

        async def api_call() -> None:
            api = await self.get_customers_api()
            await api.withdraw_customer_balance(
                change_user_balance_request=request
            )

        self._require_balance_fields(request)
        return await self.execute_with_retry(
            ApiMethod.WITHDRAW_CUSTOMER_BALANCE, api_call
        )

    async def get_loyalty_counters(
        self,
        request: GetCountersRequest,
    ) -> GetCountersResponse:
        """Счётчики лояльности гостей (кол-во заказов/суммы за периоды).

        metrics/periods — числовые enum'ы SDK (CounterMetric 0..3,
        CounterPeriod 0..12); семантика значений — по документации iiko.
        """

        async def api_call() -> GetCountersResponse:
            api = await self.get_customers_api()
            return await api.get_loyalty_counters(get_counters_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_LOYALTY_COUNTERS, api_call
        )
