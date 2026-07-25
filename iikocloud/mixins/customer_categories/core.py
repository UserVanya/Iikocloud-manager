"""CustomerCategories core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    ChangeCategoryForCustomerRequest,
    GetCategoriesRequest,
    GetCategoriesResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class CustomerCategoriesCoreMixin(_ManagerBase):
    """Core-методы CustomerCategories API."""

    async def get_customer_categories(
        self,
        request: GetCategoriesRequest,
    ) -> GetCategoriesResponse:
        """Все категории гостей организации."""

        async def api_call() -> GetCategoriesResponse:
            api = await self.get_customer_categories_api()
            return await api.get_customer_categories(
                get_categories_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_CUSTOMER_CATEGORIES, api_call
        )

    async def add_customer_category(
        self,
        request: ChangeCategoryForCustomerRequest,
    ) -> None:
        """Добавить категорию клиенту (object-ответ -> None)."""

        async def api_call() -> None:
            api = await self.get_customer_categories_api()
            await api.add_customer_category(
                change_category_for_customer_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.ADD_CUSTOMER_CATEGORY, api_call
        )

    async def remove_customer_category(
        self,
        request: ChangeCategoryForCustomerRequest,
    ) -> None:
        """Удалить категорию у клиента (object-ответ -> None)."""

        async def api_call() -> None:
            api = await self.get_customer_categories_api()
            await api.remove_customer_category(
                change_category_for_customer_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.REMOVE_CUSTOMER_CATEGORY, api_call
        )
