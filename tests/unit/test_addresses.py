"""Unit tests for Addresses domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
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

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_addresses_api"

METHODS: list[tuple[str, object, str, type]] = [
    (
        "get_cities",
        CitiesRequest(organization_ids=[ORG_ID]),
        "cities_request",
        CitiesResponse,
    ),
    (
        "get_regions",
        RegionsRequest(organization_ids=[ORG_ID]),
        "regions_request",
        RegionsResponse,
    ),
    (
        "get_streets_by_city",
        StreetsByCityRequest(organization_id=ORG_ID, city_id=ORG_ID),
        "streets_by_city_request",
        StreetsResponse,
    ),
    (
        "get_streets_by_id",
        StreetsByIdRequest(organization_id=ORG_ID, ids=[ORG_ID]),
        "streets_by_id_request",
        StreetsByIdResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_addresses_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """Все 4 метода проксируют response с request-моделью."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})
