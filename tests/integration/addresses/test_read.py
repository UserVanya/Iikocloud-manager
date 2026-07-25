"""Интеграционные read-тесты Addresses API (read-секция).

Запуск:
    uv run pytest tests/integration/addresses -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
import pytest_asyncio
from iikocloud_client import (
    CitiesRequest,
    RegionsRequest,
    StreetsByCityRequest,
    StreetsByIdRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


@pytest_asyncio.fixture(loop_scope="session")
async def first_city_id(
    manager: IikoCloudApiClientManager, organization_id: UUID
) -> UUID:
    """Первый город организации (skip, если городов нет)."""
    response = await manager.get_cities(
        CitiesRequest(organization_ids=[organization_id])
    )
    cities = [
        city
        for org in response.cities or []
        for city in org.items or []
        if not city.is_deleted
    ]
    if not cities:
        pytest.skip("Нет городов у организации read-стенда")
    return cities[0].id


class TestAddressesRead:
    async def test_get_cities_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_cities(
            CitiesRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.cities is not None

    async def test_get_regions_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_regions(
            RegionsRequest(organization_ids=[organization_id])
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.regions is not None

    async def test_get_streets_by_city_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        first_city_id: UUID,
    ) -> None:
        response = await manager.get_streets_by_city(
            StreetsByCityRequest(
                organization_id=organization_id, city_id=first_city_id
            )
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.streets is not None

    async def test_get_streets_by_id_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        first_city_id: UUID,
    ) -> None:
        streets_response = await manager.get_streets_by_city(
            StreetsByCityRequest(
                organization_id=organization_id, city_id=first_city_id
            )
        )
        streets = [
            s for s in streets_response.streets or [] if not s.is_deleted
        ]
        if not streets:
            pytest.skip("Нет улиц в городе read-стенда")

        response = await manager.get_streets_by_id(
            StreetsByIdRequest(
                organization_id=organization_id, ids=[streets[0].id]
            )
        )

        assert response is not None
        assert response.streets is not None
        if response.streets:
            street = response.streets[0]
            assert street.id is not None
            assert street.city_id is not None
            assert isinstance(street.street_name, str)
