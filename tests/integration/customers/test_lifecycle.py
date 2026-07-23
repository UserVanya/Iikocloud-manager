"""Интеграционный lifecycle-тест Customers API (write-секция).

Полный цикл: create → get by phone → delete → restore → cleanup delete.
Только write-credentials (маркер ``write``); read-ключ не затрагивается.

Запуск:
    uv run pytest -m "write and lifecycle" -v
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

import pytest
from iikocloud_client import (
    CreateOrUpdateCustomerRequest,
    DeleteCustomersRequest,
    RestoreCustomersRequest,
)
from iikocloud_client.exceptions import ApiException

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone

logger = logging.getLogger(__name__)

# Короткая пауза между write-вызовами — меньше шансов упереться в rate limit.
_API_PAUSE_SEC = 1.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.write,
    pytest.mark.lifecycle,
    pytest.mark.asyncio(loop_scope="session"),
]


def _is_crm_unavailable(exc: BaseException) -> bool:
    """Write-стенд без CRM: Transport_WrongCrmId / Common_OrganizationNotFound."""
    body = getattr(exc, "body", None) or str(exc)
    return (
        "Transport_WrongCrmId" in body
        or "Common_OrganizationNotFound" in body
        or "Organization not found" in body
    )


class TestCustomerLifecycle:
    """create → find → delete → restore → cleanup на write-стенде."""

    async def test_customer_create_delete_restore_lifecycle(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
    ) -> None:
        """Полный lifecycle клиента с уникальным телефоном и финальной очисткой."""
        phone = generate_random_phone()
        customer_id: UUID | None = None

        try:
            # 1. Создать клиента со случайным телефоном
            try:
                create_response = await manager.create_or_update_customer(
                    CreateOrUpdateCustomerRequest(
                        organization_id=organization_id,
                        phone=phone,
                        name="Lifecycle Test Customer",
                    )
                )
            except ApiException as exc:
                if _is_crm_unavailable(exc):
                    pytest.skip(
                        "Write-секция config.test.yml: организация без CRM "
                        f"(organization_id={organization_id}). "
                        "Нужен write-ключ со стендом Loyalty/CRM."
                    )
                raise

            assert create_response is not None
            assert create_response.id is not None
            customer_id = create_response.id

            await asyncio.sleep(_API_PAUSE_SEC)

            # 2. Найти по телефону
            found = await manager.get_customer_by_phone(organization_id, phone)
            assert found is not None
            assert found.id == customer_id
            assert found.phone == phone

            await asyncio.sleep(_API_PAUSE_SEC)

            # 3. Логическое удаление
            delete_response = await manager.delete_customers(
                DeleteCustomersRequest(
                    organization_id=organization_id,
                    customer_ids=[customer_id],
                )
            )
            assert delete_response is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # 4. Восстановление
            restore_response = await manager.restore_customers(
                RestoreCustomersRequest(
                    organization_id=organization_id,
                    customer_ids=[customer_id],
                )
            )
            assert restore_response is not None

            await asyncio.sleep(_API_PAUSE_SEC)

            # После restore клиент снова доступен по телефону
            restored = await manager.get_customer_by_phone(organization_id, phone)
            assert restored is not None
            assert restored.id == customer_id

        finally:
            # 5. Финальная очистка — не оставляем тестового клиента на стенде
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
                    logger.warning(
                        "Cleanup delete failed for customer %s: %s",
                        customer_id,
                        exc,
                    )
