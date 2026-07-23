"""Customers core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    AddCustomerToProgramRequest,
    AddCustomerToProgramResponse,
    AddMagnetCardRequest,
    CreateOrUpdateCustomerRequest,
    CreateOrUpdateCustomerResponse,
    DeleteCustomersRequest,
    DeleteCustomersResponse,
    DeleteMagnetCardRequest,
    GetCustomerInfoRequest,
    GetCustomerInfoResponse,
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
