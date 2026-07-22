"""Интеграционные read-тесты Dictionaries API.

Запуск:
    uv run pytest tests/integration/dictionaries -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestDictionariesRead:
    """Словари через get_*_by_organization (Locked Names)."""

    async def test_get_cancel_causes_by_organization(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """get_cancel_causes_by_organization возвращает cancel_causes."""
        response = await manager.get_cancel_causes_by_organization(
            organization_id
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.cancel_causes is not None

    async def test_get_delivery_order_types_by_organization(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """get_delivery_order_types_by_organization возвращает order_types."""
        response = await manager.get_delivery_order_types_by_organization(
            organization_id
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.order_types is not None

    async def test_get_payment_types_by_organization(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """get_payment_types_by_organization возвращает payment_types."""
        response = await manager.get_payment_types_by_organization(
            organization_id
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.payment_types is not None

    async def test_get_discounts_by_organization(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """get_discounts_by_organization возвращает discounts."""
        response = await manager.get_discounts_by_organization(organization_id)

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.discounts is not None

    async def test_get_removal_types_by_organization(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """get_removal_types_by_organization возвращает removal_types."""
        response = await manager.get_removal_types_by_organization(
            organization_id
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.removal_types is not None

    async def test_get_tips_types(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """get_tips_types возвращает tips_types (без organization_id)."""
        response = await manager.get_tips_types()

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.tips_types is not None
