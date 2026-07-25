"""Интеграционные тесты CustomerCategories (write-секция).

structure-only: get_customer_categories (test_server).
danger_write: add -> remove на свежем тестовом клиенте (cleanup в finally).

Запуск:
    uv run pytest tests/integration/customers/test_categories.py -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    ChangeCategoryForCustomerRequest,
    CreateOrUpdateCustomerRequest,
    DeleteCustomersRequest,
    GetCategoriesRequest,
)
from iikocloud_client.exceptions import ApiException

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0


def _is_crm_unavailable(exc: BaseException) -> bool:
    body = getattr(exc, "body", None) or str(exc)
    return (
        "Transport_WrongCrmId" in body
        or "Common_OrganizationNotFound" in body
        or "Organization not found" in body
    )


class TestGetCustomerCategories:
    pytestmark = [
        pytest.mark.integration,
        pytest.mark.slow,
        pytest.mark.test_server,
        pytest.mark.asyncio(loop_scope="session"),
    ]

    async def test_get_customer_categories_structure(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        response = await manager.get_customer_categories(
            GetCategoriesRequest(organization_id=organization_id)
        )

        assert response is not None
        assert response.guest_categories is not None


class TestCategoryLifecycle:
    pytestmark = [
        pytest.mark.integration,
        pytest.mark.slow,
        pytest.mark.danger_write,
        pytest.mark.asyncio(loop_scope="session"),
    ]

    async def test_add_and_remove_category(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        # category_id — первая активная категория стенда
        categories = await manager.get_customer_categories(
            GetCategoriesRequest(organization_id=organization_id)
        )
        active = [
            c
            for c in categories.guest_categories or []
            if c.is_active and c.id is not None
        ]
        if not active:
            pytest.skip("Нет активных категорий на write-стенде")
        category_id = active[0].id

        customer_id: UUID | None = None
        try:
            created = await manager.create_or_update_customer(
                CreateOrUpdateCustomerRequest(
                    organization_id=organization_id,
                    phone=generate_random_phone(),
                    name="Category Test",
                )
            )
            customer_id = created.id
            assert customer_id is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            try:
                await manager.add_customer_category(
                    ChangeCategoryForCustomerRequest(
                        category_id=category_id,
                        customer_id=customer_id,
                        organization_id=organization_id,
                    )
                )
                await asyncio.sleep(_API_PAUSE_SEC)
                await manager.remove_customer_category(
                    ChangeCategoryForCustomerRequest(
                        category_id=category_id,
                        customer_id=customer_id,
                        organization_id=organization_id,
                    )
                )
            except ApiException as exc:
                if _is_crm_unavailable(exc):
                    pytest.skip(f"Write-стенд без CRM: {exc}")
                raise
        finally:
            if customer_id is not None:
                try:
                    await asyncio.sleep(_API_PAUSE_SEC)
                    await manager.delete_customers(
                        DeleteCustomersRequest(
                            organization_id=organization_id,
                            customer_ids=[customer_id],
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Cleanup failed: %s", exc)
