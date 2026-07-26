"""Structure-only read-тесты BanquetsReserves (write-секция через test_server)."""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import pytest
from iikocloud_client import (
    GetOrganizationsRequest,
    GetRestaurantSectionsRequest,
    GetRestaurantSectionsWorkloadRequest,
    GetTerminalGroupsByOrganizationsRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.test_server,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestBanquetsRead:
    async def test_available_organizations_structure(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        response = await manager.get_reserve_available_organizations(
            GetOrganizationsRequest()
        )
        assert response is not None
        assert response.organizations is not None

    async def test_reserve_terminal_groups_structure(
        self, manager: IikoCloudApiClientManager, organization_id: UUID
    ) -> None:
        response = await manager.get_reserve_terminal_groups(
            GetTerminalGroupsByOrganizationsRequest(
                organization_ids=[organization_id]
            )
        )
        assert response is not None
        assert response.terminal_groups is not None

    async def test_restaurant_sections_structure(
        self,
        manager: IikoCloudApiClientManager,
        live_terminal_group_id: UUID,
    ) -> None:
        response = await manager.get_reserve_restaurant_sections(
            GetRestaurantSectionsRequest(
                terminal_group_ids=[live_terminal_group_id]
            )
        )
        assert response is not None
        assert response.restaurant_sections is not None
        assert isinstance(response.revision, int)

    async def test_sections_workload_structure(
        self,
        manager: IikoCloudApiClientManager,
        live_terminal_group_id: UUID,
    ) -> None:
        sections = await manager.get_reserve_restaurant_sections(
            GetRestaurantSectionsRequest(
                terminal_group_ids=[live_terminal_group_id]
            )
        )
        if not sections.restaurant_sections:
            pytest.skip("Нет секций зала на write-стенде")
        response = await manager.get_restaurant_sections_workload(
            GetRestaurantSectionsWorkloadRequest(
                restaurant_section_ids=[sections.restaurant_sections[0].id],
                date_from=datetime.now().strftime("%Y-%m-%d 00:00:00.000"),
            )
        )
        assert response is not None
        assert response.reserves is not None
