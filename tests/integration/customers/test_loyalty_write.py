"""Интеграционные danger_write-тесты лояльности (write-секция).

Карты: add -> remove. Баланс: hold -> cancel_hold и top_up -> withdraw.
Требуют write-стенд с Loyalty/CRM и кошельком у тестового клиента;
при отсутствии — skip с явной причиной.

Запуск:
    uv run pytest tests/integration/customers/test_loyalty_write.py -v -m danger_write
"""

# mypy: disable-error-code="no-untyped-def"

from __future__ import annotations

import asyncio
import logging
import os
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from iikocloud_client import (
    AddCustomerToProgramRequest,
    AddMagnetCardRequest,
    CancelHoldMoneyRequest,
    ChangeUserBalanceRequest,
    CreateOrUpdateCustomerRequest,
    DeleteCustomersRequest,
    DeleteMagnetCardRequest,
    HoldMoneyRequest,
)
from iikocloud_client.exceptions import ApiException
from yaml import CSafeLoader
from yaml import load as yaml_load

from iikocloud import IikoCloudApiClientManager
from tests.conftest import generate_random_phone

logger = logging.getLogger(__name__)

_API_PAUSE_SEC = 1.0
_WALLET_POLL_ATTEMPTS = 5
_WALLET_POLL_INTERVAL_SEC = 2.0

pytestmark = [
    pytest.mark.integration,
    pytest.mark.slow,
    pytest.mark.danger_write,
    pytest.mark.asyncio(loop_scope="session"),
]


def _is_crm_unavailable(exc: BaseException) -> bool:
    body = getattr(exc, "body", None) or str(exc)
    return (
        "Transport_WrongCrmId" in body
        or "Common_OrganizationNotFound" in body
        or "Organization not found" in body
    )


def _is_loyalty_unavailable(exc: BaseException) -> bool:
    """Стенд без программ лояльности/кошельков."""
    body = getattr(exc, "body", None) or str(exc)
    return (
        "Loyalty" in body
        or "wallet" in body.lower()
        or "program" in body.lower()
        or "CorporateNutrition" in body
    )


@pytest_asyncio.fixture(loop_scope="session")
async def test_customer(
    manager: IikoCloudApiClientManager, organization_id: UUID
):
    """Тестовый клиент на write-стенде; удаляется после теста."""
    customer_id: UUID | None = None
    try:
        response = await manager.create_or_update_customer(
            CreateOrUpdateCustomerRequest(
                organization_id=organization_id,
                phone=generate_random_phone(),
                name="Loyalty Write Test",
            )
        )
        customer_id = response.id
        yield customer_id
    except ApiException as exc:
        if _is_crm_unavailable(exc):
            pytest.skip("Write-стенд без CRM/Loyalty")
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


class TestMagnetCards:
    async def test_add_and_remove_magnet_card(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
    ) -> None:
        card_number = f"9{uuid4().int % 10**15:015d}"
        card_track = f"track-{uuid4().hex[:12]}"
        try:
            await manager.add_customer_magnet_card(
                AddMagnetCardRequest(
                    card_number=card_number,
                    card_track=card_track,
                    customer_id=test_customer,
                    organization_id=organization_id,
                )
            )
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.remove_customer_magnet_card(
                DeleteMagnetCardRequest(
                    card_track=card_track,
                    customer_id=test_customer,
                    organization_id=organization_id,
                )
            )
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд не поддерживает карты: {exc}")
            raise


class TestBalance:
    async def _wallet_id(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        customer_id: UUID,
    ) -> UUID:
        """Первый кошелёк клиента из get_customer_info (wallet_balances).

        Поллинг: свежесозданный клиент появляется в CRM-индексе не сразу
        (Transport_WrongCustomerId первые секунды после create).
        """
        info = None
        for attempt in range(_WALLET_POLL_ATTEMPTS):
            await asyncio.sleep(_WALLET_POLL_INTERVAL_SEC)
            try:
                info = await manager.get_customer_by_id(organization_id, customer_id)
                break
            except ApiException as exc:
                if _is_crm_unavailable(exc):
                    raise
                if attempt == _WALLET_POLL_ATTEMPTS - 1:
                    raise
        assert info is not None
        balances = info.wallet_balances or []
        if not balances or balances[0].id is None:
            pytest.skip("У тестового клиента нет кошелька лояльности")
        return balances[0].id

    async def test_hold_and_cancel_balance(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
    ) -> None:
        wallet_id = await self._wallet_id(manager, organization_id, test_customer)
        amount = 1.0
        try:
            # hold требует достаточный баланс: сначала top_up, в конце withdraw
            await manager.top_up_customer_balance(
                ChangeUserBalanceRequest(
                    organization_id=organization_id,
                    customer_id=test_customer,
                    wallet_id=wallet_id,
                    sum=amount,
                    comment="integration test topup before hold",
                )
            )
            await asyncio.sleep(_API_PAUSE_SEC)
            hold = await manager.hold_customer_balance(
                HoldMoneyRequest(
                    customer_id=test_customer,
                    organization_id=organization_id,
                    wallet_id=wallet_id,
                    sum=amount,
                    comment="integration test",
                    transaction_id=uuid4(),
                )
            )
            assert hold is not None
            transaction_id = hold.transaction_id
            assert transaction_id is not None
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.cancel_customer_balance_hold(
                CancelHoldMoneyRequest(
                    organization_id=organization_id,
                    transaction_id=transaction_id,
                )
            )
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.withdraw_customer_balance(
                ChangeUserBalanceRequest(
                    organization_id=organization_id,
                    customer_id=test_customer,
                    wallet_id=wallet_id,
                    sum=amount,
                    comment="integration test withdraw after hold",
                )
            )
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд не поддерживает баланс: {exc}")
            raise

    async def test_top_up_and_withdraw_balance(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
    ) -> None:
        wallet_id = await self._wallet_id(manager, organization_id, test_customer)
        amount = 1.0
        try:
            await manager.top_up_customer_balance(
                ChangeUserBalanceRequest(
                    organization_id=organization_id,
                    customer_id=test_customer,
                    wallet_id=wallet_id,
                    sum=amount,
                    comment="integration test topup",
                )
            )
            await asyncio.sleep(_API_PAUSE_SEC)
            await manager.withdraw_customer_balance(
                ChangeUserBalanceRequest(
                    organization_id=organization_id,
                    customer_id=test_customer,
                    wallet_id=wallet_id,
                    sum=amount,
                    comment="integration test withdraw",
                )
            )
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд не поддерживает баланс: {exc}")
            raise


@pytest.fixture
def loyalty_program_id() -> UUID:
    """id программы лояльности из write-секции config.test.yml.

    API требует явный programId (без него ищет corporate nutrition
    с пустым GUID и падает с 400). Программы стенда через покрытые
    методы менеджера не перечислить, поэтому id живёт в конфиге.
    """
    path = os.getenv("IIKOCLOUD_TEST_CONFIG")
    if not path:
        pytest.skip("IIKOCLOUD_TEST_CONFIG не задан")
    with open(path, "rb") as file:
        data = yaml_load(file, Loader=CSafeLoader)
    program_id = (data.get("write") or {}).get("program_id")
    if not program_id:
        pytest.skip("В write-секции config.test.yml не задан program_id")
    return UUID(str(program_id))


class TestAddCustomerToProgram:
    async def test_add_customer_to_default_program(
        self,
        manager: IikoCloudApiClientManager,
        organization_id: UUID,
        test_customer: UUID,
        loyalty_program_id: UUID,
    ) -> None:
        """Добавление клиента в программу лояльности стенда (явный programId)."""
        try:
            response = await manager.add_customer_to_program(
                AddCustomerToProgramRequest(
                    customer_id=test_customer,
                    organization_id=organization_id,
                    program_id=loyalty_program_id,
                )
            )
            assert response is not None
        except ApiException as exc:
            if _is_crm_unavailable(exc) or _is_loyalty_unavailable(exc):
                pytest.skip(f"Стенд без программ лояльности: {exc}")
            raise
