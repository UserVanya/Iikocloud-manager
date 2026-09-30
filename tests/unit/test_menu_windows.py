"""Окна чтения меню — у ключа и у организации, без ожидания (выпуск 0.3.0).

Прежде предел меню был блокирующим лимитером метода «одно меню в 120 с на ключ»: второй
вопрос ЖДАЛ до двух минут, и вызывающий бросал ждать раньше (срок ответа — 30 с). Теперь у
ключа общее окно (одно меню в 30 с), у каждой организации ключа — своё (одно в 120 с), и
менеджер не ждёт: не пора — сразу ``MenuTooEarly`` с числом секунд. «Слишком часто» (429) от
iiko ставит на паузу чтение меню всего ключа.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import MenuRequestV3

from iikocloud import MenuTooEarly, MenuWindows
from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.mixins._base import ApiMethod
from tests.unit.conftest import credentials, limits, manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_A = UUID("12345678-1234-1234-1234-123456789abc")
ORG_B = UUID("87654321-4321-4321-4321-cba987654321")
MENU_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


class Clock:
    """Монотонные часы под ручным управлением."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _windows(clock: Clock) -> MenuWindows:
    return MenuWindows(per_key_sec=30, per_organization_sec=120, pause_sec=300, clock=clock)


def test_menus_of_one_organization_share_its_window() -> None:
    clock = Clock()
    windows = _windows(clock)
    windows.take(ORG_A)
    clock.now += 60
    with pytest.raises(MenuTooEarly) as early:
        windows.take(ORG_A)
    assert early.value.seconds == 60 and early.value.reason == "organization"
    clock.now += 60
    windows.take(ORG_A)


def test_menus_of_two_organizations_share_the_key_window() -> None:
    clock = Clock()
    windows = _windows(clock)
    windows.take(ORG_A)
    clock.now += 10
    with pytest.raises(MenuTooEarly) as early:
        windows.take(ORG_B)
    assert early.value.seconds == 20 and early.value.reason == "key"
    clock.now += 20
    windows.take(ORG_B)


def test_a_refused_try_does_not_spend_the_windows() -> None:
    """Отказ «рано» окна не сдвигает: иначе частый спрашивающий не дождался бы никогда."""
    clock = Clock()
    windows = _windows(clock)
    windows.take(ORG_A)
    for _ in range(5):
        clock.now += 5
        with pytest.raises(MenuTooEarly):
            windows.take(ORG_B)
    clock.now += 5
    windows.take(ORG_B)


def test_a_pause_stops_every_menu_of_the_key() -> None:
    clock = Clock()
    windows = _windows(clock)
    windows.pause()
    with pytest.raises(MenuTooEarly) as early:
        windows.take(ORG_B)
    assert early.value.seconds == 300 and early.value.reason == "paused"
    assert windows.state()["paused_for_sec"] == 300
    clock.now += 300
    windows.take(ORG_B)
    assert windows.state()["paused_for_sec"] == 0


def test_menu_limits_change_live() -> None:
    """Правка окон действует сразу и помнит, когда меню читали в последний раз."""
    clock = Clock()
    windows = _windows(clock)
    windows.take(ORG_A)
    windows.resize(per_key_sec=10, per_organization_sec=60)
    clock.now += 30
    with pytest.raises(MenuTooEarly) as early:
        windows.take(ORG_A)
    assert early.value.seconds == 30 and early.value.reason == "organization"
    clock.now += 30
    windows.take(ORG_A)
    assert (
        windows.state()["per_key_sec"] == 10
        and windows.state()["per_organization_sec"] == 60
    )


def _request(organization_id: UUID) -> MenuRequestV3:
    return MenuRequestV3(external_menu_id=MENU_ID, organization_id=organization_id)


async def test_too_early_is_answered_without_waiting() -> None:
    manager, api = await manager_with_stub_api("_menu_api")
    api.get_external_menu_v3_by_id = AsyncMock(return_value=MagicMock())
    await manager.get_external_menu_v3_by_id(_request(ORG_A))
    with pytest.raises(MenuTooEarly) as early:
        await asyncio.wait_for(
            manager.get_external_menu_v3_by_id(_request(ORG_B)), timeout=1
        )
    assert early.value.reason == "key" and 0 < early.value.seconds <= 30
    assert api.get_external_menu_v3_by_id.await_count == 1, "рано — а в iiko спросили"


class TooMany(Exception):
    """Ответ iiko «слишком часто»."""

    status = 429


async def _stubbed(manager: IikoCloudApiClientManager) -> MagicMock:
    stub_token = MagicMock()
    stub_token.token_version = 1
    manager._token_manager = stub_token
    api = MagicMock()
    manager._menu_api = api
    return api


async def test_a_429_pauses_menus_of_that_key_only() -> None:
    ours = await IikoCloudApiClientManager.get_instance(
        credentials(api_key="ours"), limits()
    )
    theirs = await IikoCloudApiClientManager.get_instance(
        credentials(api_key="theirs"), limits()
    )
    our_api, their_api = await _stubbed(ours), await _stubbed(theirs)
    our_api.get_external_menu_v3_by_id = AsyncMock(side_effect=TooMany("слишком часто"))
    their_api.get_external_menu_v3_by_id = AsyncMock(return_value=MagicMock())

    with pytest.raises(TooMany):
        await ours.get_external_menu_v3_by_id(_request(ORG_A))
    with pytest.raises(MenuTooEarly) as early:
        await ours.get_external_menu_v3_by_id(_request(ORG_B))
    assert early.value.reason == "paused"
    assert ours.menu_state()["paused_for_sec"] > 0
    await theirs.get_external_menu_v3_by_id(_request(ORG_B))
    assert theirs.menu_state()["paused_for_sec"] == 0


async def test_set_menu_limits_moves_the_windows_and_the_method_backstop() -> None:
    """Лимитер метода меню — страховка по окну ключа: окно короче — страховка
    не держит вопрос."""
    manager, _api = await manager_with_stub_api("_menu_api")
    manager.set_menu_limits(per_key_sec=10, per_organization_sec=60)
    assert manager.menu_state()["per_key_sec"] == 10
    limiter = manager._get_method_limiter(ApiMethod.GET_EXTERNAL_MENU_V3_BY_ID)
    assert limiter._refill_rate == pytest.approx(1 / 10)


async def test_the_windows_come_from_the_config() -> None:
    from iikocloud.config_reader import IikoCloudConfig, MenuWindowsSettings

    config = IikoCloudConfig(
        api_key="from-config",
        app_id="00000000-0000-0000-0000-000000000001",
        client_secret="s",
        menu_windows=MenuWindowsSettings(per_key_sec=45, per_organization_sec=180),
    )
    manager = await IikoCloudApiClientManager.from_config(config)
    assert manager.menu_state()["per_key_sec"] == 45
    assert manager.menu_state()["per_organization_sec"] == 180
