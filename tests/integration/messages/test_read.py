"""Structure-only read-тесты Messages (write-секция через test_server)."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    CheckSmsStatusRequest,
    SmsSendingPossibilityRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestMessagesRead:
    async def test_check_sms_sending_possibility_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.check_sms_sending_possibility(
            SmsSendingPossibilityRequest(organization_id=organization_id)
        )
        assert response is not None
        assert response.status is not None

    async def test_check_sms_status_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        """По несуществующему sms_id — валидная структура statuses."""
        response = await manager.check_sms_status(
            CheckSmsStatusRequest(
                organization_id=organization_id,
                sms_ids=[UUID("00000000-0000-0000-0000-000000000001")],
            )
        )
        assert response is not None
        assert response.statuses is not None
