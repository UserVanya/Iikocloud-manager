"""Danger_write-тест reserve lifecycle (write-секция).

sections -> столик -> create_reserve -> status_by_id -> cancel (finally).

Запуск:
    uv run pytest tests/integration/banquets/test_reserve.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from uuid import UUID

import pytest
from iikocloud_client import (
    CancelReserveRequest,
    CreateReserveRequest,
    DeliveryOrderCreateRegularCustomer,
    GetRestaurantSectionsRequest,
    ReserveCancelReason,
    ReservesByIdRequest,
)

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestReserveLifecycle:
    async def test_create_read_cancel_reserve(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        live_terminal_group_id: UUID,
    ) -> None:
        # Столик из секций зала
        sections = await manager.get_reserve_restaurant_sections(
            GetRestaurantSectionsRequest(
                terminal_group_ids=[live_terminal_group_id]
            )
        )
        tables = [
            table
            for section in sections.restaurant_sections or []
            for table in section.tables or []
            if not getattr(table, "is_deleted", False)
        ]
        if not tables:
            pytest.skip("Нет столиков на write-стенде")
        table_id = tables[0].id

        reserve_id: UUID | None = None
        try:
            # create (estimatedStartTime = завтра + 1ч, длительность 60 мин)
            start = (datetime.now() + timedelta(days=1, hours=1)).strftime(
                "%Y-%m-%d %H:%M:%S.000"
            )
            create_response = await manager.create_reserve(
                CreateReserveRequest(
                    organization_id=organization_id,
                    terminal_group_id=live_terminal_group_id,
                    phone=generate_random_phone(),
                    customer=DeliveryOrderCreateRegularCustomer(
                        type="regular", name="Reserve Test"
                    ),
                    estimated_start_time=start,
                    duration_in_minutes=60,
                    guests_count=2,
                    should_remind=False,
                    table_ids=[table_id],
                )
            )
            assert create_response is not None
            reserve_info = create_response.reserve_info
            assert reserve_info is not None
            status_value = getattr(reserve_info.creation_status, "value", None)
            assert status_value != "Error", (
                f"Create failed: {reserve_info.error_info}"
            )
            reserve_id = reserve_info.id
            assert reserve_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # status_by_id — резерв читается
            statuses = await manager.get_reserve_statuses_by_id(
                ReservesByIdRequest(
                    organization_id=organization_id,
                    reserve_ids=[reserve_id],
                )
            )
            found = [
                r for r in statuses.reserves or [] if r.id == reserve_id
            ]
            assert found, "Резерв не найден через status_by_id"

        finally:
            # cleanup: cancel (только для статуса New)
            if reserve_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.cancel_reserve(
                        CancelReserveRequest(
                            organization_id=organization_id,
                            reserve_id=reserve_id,
                            cancel_reason=ReserveCancelReason.CLIENTREFUSED,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Cancel reserve cleanup failed for %s: %s",
                        reserve_id,
                        exc,
                    )
