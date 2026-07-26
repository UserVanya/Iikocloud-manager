"""MarketingSources core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import MarketingSourcesRequest, MarketingSourcesResponse

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class MarketingSourcesCoreMixin(_ManagerBase):
    """Core-методы MarketingSources API (read-only, iiko >= 7.2.5)."""

    async def get_marketing_sources(
        self,
        request: MarketingSourcesRequest,
    ) -> MarketingSourcesResponse:
        """Справочник источников маркетинга организаций."""

        async def api_call() -> MarketingSourcesResponse:
            api = await self.get_marketing_sources_api()
            return await api.get_marketing_sources(
                marketing_sources_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_MARKETING_SOURCES, api_call
        )
