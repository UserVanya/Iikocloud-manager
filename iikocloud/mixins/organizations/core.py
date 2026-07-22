"""Organizations core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    GetOrganizationsRequest,
    GetOrganizationsResponse,
    OrganizationsSettingsRequest,
    OrganizationsSettingsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class OrganizationsCoreMixin(_ManagerBase):
    """Core-методы Organizations API."""

    async def get_organizations(
        self,
        request: GetOrganizationsRequest | None = None,
    ) -> GetOrganizationsResponse:
        """Получить список организаций.

        Args:
            request: Параметры запроса (по умолчанию пустой GetOrganizationsRequest)

        Returns:
            Ответ со списком организаций
        """
        req = request if request is not None else GetOrganizationsRequest()

        async def api_call() -> GetOrganizationsResponse:
            api = await self.get_organizations_api()
            return await api.get_organizations(get_organizations_request=req)

        return await self.execute_with_retry(ApiMethod.GET_ORGANIZATIONS, api_call)

    async def get_organization_settings(
        self,
        request: OrganizationsSettingsRequest | None = None,
    ) -> OrganizationsSettingsResponse:
        """Получить настройки организаций.

        Args:
            request: Параметры запроса (по умолчанию пустой OrganizationsSettingsRequest)

        Returns:
            Ответ с настройками организаций
        """
        req = (
            request if request is not None else OrganizationsSettingsRequest()
        )

        async def api_call() -> OrganizationsSettingsResponse:
            api = await self.get_organizations_api()
            return await api.get_organization_settings(
                organizations_settings_request=req
            )

        return await self.execute_with_retry(
            ApiMethod.GET_ORGANIZATION_SETTINGS, api_call
        )
