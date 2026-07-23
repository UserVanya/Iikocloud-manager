"""Интеграционные read-тесты Menu API: номенклатура и комбо.

Запуск:
    uv run pytest tests/integration/menu/test_nomenclature_combos.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

from uuid import UUID

import pytest
from iikocloud_client import (
    GetCombosInfoRequest,
    NomenclatureRequest,
)

from iikocloud import IikoCloudApiClientManager

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.asyncio(loop_scope="session"),
]


class TestGetNomenclature:
    """get_nomenclature против реального API."""

    async def test_full_nomenclature_returns_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Полная выгрузка (start_revision=0): revision + списки."""
        response = await manager.get_nomenclature(
            NomenclatureRequest(organization_id=organization_id, start_revision=0)
        )

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert isinstance(response.revision, int)
        assert response.groups is not None
        assert response.products is not None
        assert response.sizes is not None

    async def test_same_revision_returns_empty_delta(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Повтор с revision из прошлого ответа -> списки пустые."""
        first = await manager.get_nomenclature(
            NomenclatureRequest(organization_id=organization_id, start_revision=0)
        )
        second = await manager.get_nomenclature(
            NomenclatureRequest(
                organization_id=organization_id,
                start_revision=first.revision,
            )
        )

        assert second.revision == first.revision
        assert second.products == [] or second.products is None


class TestGetCombosInfo:
    """get_combos_info против реального API."""

    async def test_get_combos_info_returns_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Ответ содержит категории/спецификации комбо (могут быть пустыми)."""
        response = await manager.get_combos_info(
            GetCombosInfoRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.combo_categories is not None
        assert response.combo_specifications is not None
