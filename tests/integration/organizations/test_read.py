"""Интеграционные read-тесты Organizations API.

Запуск:
    uv run pytest tests/integration/organizations -v
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


class TestGetOrganizations:
    """get_organizations против реального API (read-секция)."""

    async def test_get_organizations_returns_non_empty_list(
        self, manager: IikoCloudApiClientManager
    ) -> None:
        """get_organizations возвращает хотя бы одну организацию с id/name."""
        response = await manager.get_organizations()

        assert response is not None
        assert isinstance(response.correlation_id, UUID)
        assert response.organizations is not None
        assert len(response.organizations) > 0

        org = response.organizations[0]
        assert isinstance(org.id, UUID)
        assert isinstance(org.name, str)
        assert len(org.name) > 0
