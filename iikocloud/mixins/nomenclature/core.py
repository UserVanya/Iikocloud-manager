"""Nomenclature core mixin — техкарты v3 и справочники номенклатуры (прямые обёртки SDK).

Адреса ``/api/nomenclature/v3/assembly-chart/*`` (техкарты, описание iiko 9.8.6.3) и
``/api/nomenclature/v1/*`` (типы скидок, коды ТН ВЭД).
"""

from iikocloud_client import (
    AssemblyChartCommonResponseV3,
    AssemblyChartListRequestV3,
    AssemblyChartListResponseV3,
    AssemblyChartResponseV3,
    AssemblyChartV3SaveRequest,
    CreateRequestV3,
    DeleteRequestV3,
    DiscountTypeListRequest,
    DiscountTypeListResponse,
    GetRequestV3,
    OuterEconomicActivityNomenclatureCode,
    OuterEconomicActivityNomenclatureCodeGetRequest,
    OuterEconomicActivityNomenclatureCodeListRequest,
    OuterEconomicActivityNomenclatureCodeListResponse,
    ResolveRequestV3,
    ResolveResponseV3,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class NomenclatureCoreMixin(_ManagerBase):
    """Core-методы техкарт v3 и справочников номенклатуры."""

    async def create_nomenclature_assembly_chart_v3(
        self, request: CreateRequestV3
    ) -> AssemblyChartCommonResponseV3:
        """Создать техкарту блюда (v3).

        Свежесозданный продукт может ещё не попасть в номенклатуру — iiko ответит 502;
        дождитесь продукта в списке номенклатуры.
        """

        async def api_call() -> AssemblyChartCommonResponseV3:
            api = await self.get_nomenclature_assembly_chart_api()
            return await api.create_nomenclature_assembly_chart_v3(
                create_request_v3=request
            )

        return await self.execute_with_retry(
            ApiMethod.CREATE_NOMENCLATURE_ASSEMBLY_CHART_V3, api_call
        )

    async def update_nomenclature_assembly_chart_v3(
        self, request: AssemblyChartV3SaveRequest
    ) -> AssemblyChartCommonResponseV3:
        """Изменить техкарту (v3)."""

        async def api_call() -> AssemblyChartCommonResponseV3:
            api = await self.get_nomenclature_assembly_chart_api()
            return await api.update_nomenclature_assembly_chart_v3(
                assembly_chart_v3_save_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UPDATE_NOMENCLATURE_ASSEMBLY_CHART_V3, api_call
        )

    async def delete_nomenclature_assembly_chart_v3(
        self, request: DeleteRequestV3
    ) -> AssemblyChartCommonResponseV3:
        """Удалить техкарту (v3)."""

        async def api_call() -> AssemblyChartCommonResponseV3:
            api = await self.get_nomenclature_assembly_chart_api()
            return await api.delete_nomenclature_assembly_chart_v3(
                delete_request_v3=request
            )

        return await self.execute_with_retry(
            ApiMethod.DELETE_NOMENCLATURE_ASSEMBLY_CHART_V3, api_call
        )

    async def get_nomenclature_assembly_chart_v3(
        self, request: GetRequestV3
    ) -> AssemblyChartResponseV3:
        """Техкарта по id (v3)."""

        async def api_call() -> AssemblyChartResponseV3:
            api = await self.get_nomenclature_assembly_chart_api()
            return await api.get_nomenclature_assembly_chart_v3(get_request_v3=request)

        return await self.execute_with_retry(
            ApiMethod.GET_NOMENCLATURE_ASSEMBLY_CHART_V3, api_call
        )

    async def list_nomenclature_assembly_charts_v3(
        self, request: AssemblyChartListRequestV3
    ) -> AssemblyChartListResponseV3:
        """Список техкарт (v3)."""

        async def api_call() -> AssemblyChartListResponseV3:
            api = await self.get_nomenclature_assembly_chart_api()
            return await api.list_nomenclature_assembly_charts_v3(
                assembly_chart_list_request_v3=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_NOMENCLATURE_ASSEMBLY_CHARTS_V3, api_call
        )

    async def resolve_nomenclature_assembly_chart_v3(
        self, request: ResolveRequestV3
    ) -> ResolveResponseV3:
        """Техкарта продукта на дату в нужном виде (``view``: assembled, prepared, tree)."""

        async def api_call() -> ResolveResponseV3:
            api = await self.get_nomenclature_assembly_chart_api()
            return await api.resolve_nomenclature_assembly_chart_v3(
                resolve_request_v3=request
            )

        return await self.execute_with_retry(
            ApiMethod.RESOLVE_NOMENCLATURE_ASSEMBLY_CHART_V3, api_call
        )

    async def list_nomenclature_discount_types(
        self, request: DiscountTypeListRequest
    ) -> DiscountTypeListResponse:
        """Справочник типов скидок (по 1..1000 за раз)."""

        async def api_call() -> DiscountTypeListResponse:
            api = await self.get_nomenclature_directories_api()
            return await api.list_nomenclature_discount_types(
                discount_type_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_NOMENCLATURE_DISCOUNT_TYPES, api_call
        )

    async def get_nomenclature_outer_economic_activity_code(
        self, request: OuterEconomicActivityNomenclatureCodeGetRequest
    ) -> OuterEconomicActivityNomenclatureCode:
        """Код ТН ВЭД по id."""

        async def api_call() -> OuterEconomicActivityNomenclatureCode:
            api = await self.get_nomenclature_directories_api()
            return await api.get_nomenclature_outer_economic_activity_code(
                outer_economic_activity_nomenclature_code_get_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_NOMENCLATURE_OUTER_ECONOMIC_ACTIVITY_CODE, api_call
        )

    async def list_nomenclature_outer_economic_activity_codes(
        self, request: OuterEconomicActivityNomenclatureCodeListRequest
    ) -> OuterEconomicActivityNomenclatureCodeListResponse:
        """Справочник кодов ТН ВЭД."""

        async def api_call() -> OuterEconomicActivityNomenclatureCodeListResponse:
            api = await self.get_nomenclature_directories_api()
            return await api.list_nomenclature_outer_economic_activity_codes(
                outer_economic_activity_nomenclature_code_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_NOMENCLATURE_OUTER_ECONOMIC_ACTIVITY_CODES, api_call
        )
