"""Addresses core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CitiesRequest,
    CitiesResponse,
    RegionsRequest,
    RegionsResponse,
    StreetsByCityRequest,
    StreetsByIdRequest,
    StreetsByIdResponse,
    StreetsResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class AddressesCoreMixin(_ManagerBase):
    """Core-методы Addresses API (гео-справочники, read-only)."""

    async def get_cities(self, request: CitiesRequest) -> CitiesResponse:
        """Города организаций (ответ сгруппирован per-organization)."""

        async def api_call() -> CitiesResponse:
            api = await self.get_addresses_api()
            return await api.get_cities(cities_request=request)

        return await self.execute_with_retry(ApiMethod.GET_CITIES, api_call)

    async def get_regions(self, request: RegionsRequest) -> RegionsResponse:
        """Регионы (районы) организаций."""

        async def api_call() -> RegionsResponse:
            api = await self.get_addresses_api()
            return await api.get_regions(regions_request=request)

        return await self.execute_with_retry(ApiMethod.GET_REGIONS, api_call)

    async def get_streets_by_city(
        self, request: StreetsByCityRequest
    ) -> StreetsResponse:
        """Улицы города (одиночная organization_id)."""

        async def api_call() -> StreetsResponse:
            api = await self.get_addresses_api()
            return await api.get_streets_by_city(
                streets_by_city_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_STREETS_BY_CITY, api_call
        )

    async def get_streets_by_id(
        self, request: StreetsByIdRequest
    ) -> StreetsByIdResponse:
        """Улицы по ids или classifierIds (correlation_id в ответе optional)."""

        async def api_call() -> StreetsByIdResponse:
            api = await self.get_addresses_api()
            return await api.get_streets_by_id(streets_by_id_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_STREETS_BY_ID, api_call
        )
