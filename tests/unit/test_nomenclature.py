"""Unit tests for Nomenclature domain mixins (техкарты v3, типы скидок, коды ТН ВЭД)."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
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

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ID = UUID("12345678-1234-1234-1234-123456789abc")
CHARTS = "_nomenclature_assembly_chart_api"
DIRECTORIES = "_nomenclature_directories_api"

METHODS: list[tuple[str, object, str, type, str]] = [
    (
        "create_nomenclature_assembly_chart_v3",
        CreateRequestV3.model_construct(date_to="2026-12-31"),
        "create_request_v3",
        AssemblyChartCommonResponseV3,
        CHARTS,
    ),
    (
        "update_nomenclature_assembly_chart_v3",
        AssemblyChartV3SaveRequest.model_construct(date_to="2026-12-31"),
        "assembly_chart_v3_save_request",
        AssemblyChartCommonResponseV3,
        CHARTS,
    ),
    (
        "delete_nomenclature_assembly_chart_v3",
        DeleteRequestV3.model_construct(),
        "delete_request_v3",
        AssemblyChartCommonResponseV3,
        CHARTS,
    ),
    (
        "get_nomenclature_assembly_chart_v3",
        GetRequestV3.model_construct(),
        "get_request_v3",
        AssemblyChartResponseV3,
        CHARTS,
    ),
    (
        "list_nomenclature_assembly_charts_v3",
        AssemblyChartListRequestV3.model_construct(),
        "assembly_chart_list_request_v3",
        AssemblyChartListResponseV3,
        CHARTS,
    ),
    (
        "resolve_nomenclature_assembly_chart_v3",
        ResolveRequestV3(product_id=ID, var_date="2026-10-13", view="tree"),
        "resolve_request_v3",
        ResolveResponseV3,
        CHARTS,
    ),
    (
        "list_nomenclature_discount_types",
        DiscountTypeListRequest(limit=100),
        "discount_type_list_request",
        DiscountTypeListResponse,
        DIRECTORIES,
    ),
    (
        "get_nomenclature_outer_economic_activity_code",
        OuterEconomicActivityNomenclatureCodeGetRequest.model_construct(),
        "outer_economic_activity_nomenclature_code_get_request",
        OuterEconomicActivityNomenclatureCode,
        DIRECTORIES,
    ),
    (
        "list_nomenclature_outer_economic_activity_codes",
        OuterEconomicActivityNomenclatureCodeListRequest.model_construct(),
        "outer_economic_activity_nomenclature_code_list_request",
        OuterEconomicActivityNomenclatureCodeListResponse,
        DIRECTORIES,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls", "api_slot"), METHODS
)
async def test_nomenclature_methods_delegate(
    method_name: str,
    sdk_request: object,
    sdk_kwarg: str,
    response_cls: type,
    api_slot: str,
) -> None:
    """Все 9 методов проксируют запрос в одноимённый метод SDK и отдают ответ."""
    manager, mock_api = await manager_with_stub_api(api_slot)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
