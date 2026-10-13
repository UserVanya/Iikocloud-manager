"""Unit tests for Reporting domain mixins (план выручки, OLAP-пресеты)."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    GetIncomePlanRequest,
    GetIncomePlanResponse,
    GetOlapReportResponse,
    OlapPreset,
    OlapPresetReportRequest,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")


async def test_get_income_plan_delegates() -> None:
    manager, mock_api = await manager_with_stub_api("_reporting_income_plan_api")
    request = GetIncomePlanRequest(
        organization_id=ORG_ID, date_from=date(2026, 10, 1), date_to=date(2026, 10, 31)
    )
    response = MagicMock(spec=GetIncomePlanResponse)
    mock_api.get_income_plan = AsyncMock(return_value=response)

    assert await manager.get_income_plan(request) is response
    mock_api.get_income_plan.assert_awaited_once_with(get_income_plan_request=request)


async def test_list_olap_presets_sends_empty_body() -> None:
    manager, mock_api = await manager_with_stub_api("_reporting_olap_api")
    presets = [OlapPreset(preset_id="p1", name="Выручка")]
    mock_api.list_olap_presets = AsyncMock(return_value=presets)

    assert await manager.list_olap_presets() == presets
    mock_api.list_olap_presets.assert_awaited_once_with(body={})


async def test_get_olap_preset_report_delegates() -> None:
    manager, mock_api = await manager_with_stub_api("_reporting_olap_api")
    request = OlapPresetReportRequest(
        preset_id="p1", date_from="2026-10-01", date_to="2026-10-02"
    )
    response = MagicMock(spec=GetOlapReportResponse)
    mock_api.get_olap_preset_report = AsyncMock(return_value=response)

    assert await manager.get_olap_preset_report(request) is response
    mock_api.get_olap_preset_report.assert_awaited_once_with(
        olap_preset_report_request=request
    )
