"""Reporting core mixin — план выручки и OLAP-пресеты (/api/reporting/v1).

Не путать с ``ReportCoreMixin`` (``/api/1/loyalty/iiko/customer/transactions/*`` —
транзакции гостя программы лояльности).
"""

from iikocloud_client import (
    GetIncomePlanRequest,
    GetIncomePlanResponse,
    GetOlapReportResponse,
    OlapPreset,
    OlapPresetReportRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class ReportingCoreMixin(_ManagerBase):
    """Core-методы отчётов /api/reporting/v1."""

    async def get_income_plan(self, request: GetIncomePlanRequest) -> GetIncomePlanResponse:
        """План выручки организации по дням за период (даты включительно)."""

        async def api_call() -> GetIncomePlanResponse:
            api = await self.get_reporting_income_plan_api()
            return await api.get_income_plan(get_income_plan_request=request)

        return await self.execute_with_retry(ApiMethod.GET_INCOME_PLAN, api_call)

    async def list_olap_presets(self) -> list[OlapPreset]:
        """Сохранённые владельцем OLAP-пресеты (id и название)."""

        async def api_call() -> list[OlapPreset]:
            api = await self.get_reporting_olap_api()
            return await api.list_olap_presets(body={})

        return await self.execute_with_retry(ApiMethod.LIST_OLAP_PRESETS, api_call)

    async def get_olap_preset_report(
        self, request: OlapPresetReportRequest
    ) -> GetOlapReportResponse:
        """Данные OLAP-отчёта по сохранённому пресету за период (``yyyy-MM-dd``)."""

        async def api_call() -> GetOlapReportResponse:
            api = await self.get_reporting_olap_api()
            return await api.get_olap_preset_report(olap_preset_report_request=request)

        return await self.execute_with_retry(ApiMethod.GET_OLAP_PRESET_REPORT, api_call)
