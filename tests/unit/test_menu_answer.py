"""Меню V3 вместе с ответом iiko байт в байт (выпуск 0.4.0).

Панели сотрудника нужен не только разобранный MenuV3, но и тело ответа iiko как есть —
чтобы показать, что именно прислал iiko. ``get_external_menu_v3_by_id_with_answer`` читает
тот же адрес тем же путём, что ``get_external_menu_v3_by_id``: те же окна, тот же предел
метода, тот же повтор после 401 и пауза после 429 — и одним запросом на попытку.

Здесь настоящий клиент SDK ходит в поддельный iiko на уровне HTTP (``httpx.MockTransport``):
так проверяется весь путь — запрос, тело ответа, разбор моделью и исключения SDK.
"""

import gzip
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import httpx
import pytest
from iikocloud_client import MenuRequestV3, MenuV3
from iikocloud_client.exceptions import ApiException
from pydantic import ValidationError

from iikocloud import MenuAnswerUnreadable, MenuTooEarly, MenuV3Answer
from iikocloud.api_client_manager import IikoCloudApiClientManager
from iikocloud.mixins._base import ApiMethod
from tests.unit.conftest import manager_with_stub_token

pytestmark = pytest.mark.unit

ORG_A = UUID("12345678-1234-1234-1234-123456789abc")
ORG_B = UUID("87654321-4321-4321-4321-cba987654321")
MENU_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
JSON = "application/json; charset=utf-8"

# Тело — как его пишет iiko: перенос строки, два пробела, кириллица без \u-экранов.
# Модель, собранная обратно в JSON, дала бы другие байты — так видно, что отдано тело,
# а не пересборка.
MENU_BODY = (
    '{"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",\n'
    '  "name": "Меню «Шу-Шу»", "description": "Хлеб, выпечка и кофе — с 8:00"}'
).encode()
HTML_ERROR = "<html>ошибка шлюза</html>".encode()


class FakeIiko:
    """Поддельный iiko: отдаёт заготовленные ответы по очереди и помнит запросы."""

    def __init__(self, *responses: httpx.Response) -> None:
        self._responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responses.pop(0)


def _menu(body: bytes = MENU_BODY, content_type: str = JSON) -> httpx.Response:
    return httpx.Response(200, headers={"Content-Type": content_type}, content=body)


def _request(organization_id: UUID = ORG_A) -> MenuRequestV3:
    return MenuRequestV3(external_menu_id=MENU_ID, organization_id=organization_id)


async def _manager_over(iiko: FakeIiko) -> tuple[IikoCloudApiClientManager, MagicMock]:
    """Настоящий менеджер и клиент SDK; сеть — поддельный iiko, токен — заглушка."""
    manager, token = await manager_with_stub_token()
    manager._api_client.rest_client.pool_manager = httpx.AsyncClient(
        transport=httpx.MockTransport(iiko)
    )
    return manager, token


async def test_the_answer_is_the_menu_and_the_body_byte_for_byte() -> None:
    iiko = FakeIiko(_menu())
    manager, _token = await _manager_over(iiko)

    answer = await manager.get_external_menu_v3_by_id_with_answer(_request())

    assert isinstance(answer, MenuV3Answer)
    assert isinstance(answer.menu, MenuV3)
    assert answer.menu.name == "Меню «Шу-Шу»"
    assert answer.raw == MENU_BODY, "тело ответа не то, что прислал iiko"
    assert answer.content_type == JSON
    assert iiko.requests[0].url.path == "/api/menu/v3/by_id"
    assert "raw=" not in repr(answer), "мегабайты меню не должны попадать в repr"


async def test_a_gzipped_answer_gives_the_body_iiko_wrote() -> None:
    """Сжатие передачи снимает HTTP-клиент; ``raw`` — тело, которое iiko сжал."""
    gzipped = httpx.Response(
        200,
        headers={"Content-Type": JSON, "Content-Encoding": "gzip"},
        content=gzip.compress(MENU_BODY),
    )
    manager, _token = await _manager_over(FakeIiko(gzipped))

    answer = await manager.get_external_menu_v3_by_id_with_answer(_request())

    assert answer.raw == MENU_BODY
    assert answer.menu.description == "Хлеб, выпечка и кофе — с 8:00"


async def test_one_read_is_one_request_to_iiko() -> None:
    """Байты и меню — из одного ответа: второй раз за телом в iiko не ходят."""
    iiko = FakeIiko(_menu(), _menu())
    manager, _token = await _manager_over(iiko)

    await manager.get_external_menu_v3_by_id_with_answer(_request())

    assert len(iiko.requests) == 1


@pytest.mark.parametrize(
    "answer_first", [True, False], ids=["answer-then-menu", "menu-then-answer"]
)
async def test_the_answer_and_the_menu_share_the_organization_window(
    answer_first: bool,
) -> None:
    iiko = FakeIiko(_menu(), _menu())
    manager, _token = await _manager_over(iiko)
    reads = [
        manager.get_external_menu_v3_by_id_with_answer,
        manager.get_external_menu_v3_by_id,
    ]
    first, second = reads if answer_first else reversed(reads)

    await first(_request())
    with pytest.raises(MenuTooEarly) as early:
        await second(_request())

    assert early.value.reason == "organization"
    assert len(iiko.requests) == 1, "окно закрыто — а в iiko спросили"


async def test_the_answer_goes_through_the_menu_method_limit() -> None:
    """Тот же предел метода, что у меню: свой ключ дал бы чтению с ответом своё окно."""
    manager, _token = await _manager_over(FakeIiko(_menu()))

    async def _passthrough(method, api_call):  # noqa: ANN001
        return await api_call()

    manager.execute_with_retry = AsyncMock(side_effect=_passthrough)

    await manager.get_external_menu_v3_by_id_with_answer(_request())

    manager.execute_with_retry.assert_awaited_once()
    assert (
        manager.execute_with_retry.await_args.args[0]
        is ApiMethod.GET_EXTERNAL_MENU_V3_BY_ID
    )


async def test_a_429_on_the_answer_pauses_menus_of_the_key() -> None:
    too_many = httpx.Response(429, headers={"Content-Type": JSON}, content=b"{}")
    manager, _token = await _manager_over(FakeIiko(too_many))

    with pytest.raises(ApiException) as error:
        await manager.get_external_menu_v3_by_id_with_answer(_request(ORG_A))

    assert error.value.status == 429
    assert not isinstance(error.value, MenuAnswerUnreadable)
    assert manager.menu_state()["paused_for_sec"] > 0
    with pytest.raises(MenuTooEarly) as early:
        await manager.get_external_menu_v3_by_id(_request(ORG_B))
    assert early.value.reason == "paused"


async def test_a_401_on_the_answer_refreshes_the_token_and_asks_once_more() -> None:
    expired = httpx.Response(
        401,
        headers={"Content-Type": JSON},
        content=(
            b'{"correlationId": "00000000-0000-0000-0000-000000000002",'
            b' "errorDescription": "token expired"}'
        ),
    )
    iiko = FakeIiko(expired, _menu())
    manager, token = await _manager_over(iiko)
    token.refresh_token_if_401 = AsyncMock(return_value=True)

    answer = await manager.get_external_menu_v3_by_id_with_answer(_request())

    assert answer.raw == MENU_BODY
    token.refresh_token_if_401.assert_awaited_once()
    assert len(iiko.requests) == 2


async def test_an_unreadable_menu_is_raised_with_the_body() -> None:
    unreadable = '{"id": 42, "description": "нет имени"}'.encode()
    manager, _token = await _manager_over(FakeIiko(_menu(unreadable)))

    with pytest.raises(MenuAnswerUnreadable) as error:
        await manager.get_external_menu_v3_by_id_with_answer(_request())

    assert error.value.raw == unreadable
    assert error.value.content_type == JSON
    assert isinstance(error.value.__cause__, ValidationError)
    assert error.value.original_error is error.value.__cause__
    assert "не разобран" in str(error.value)
    assert manager.menu_state()["paused_for_sec"] == 0, "неразобранное меню — не 429"


@pytest.mark.parametrize(
    ("body", "content_type"),
    [
        (b"null", JSON),
        (HTML_ERROR, JSON),
        (HTML_ERROR, "text/html"),
    ],
    ids=["null", "not-json", "html"],
)
async def test_a_success_without_a_menu_is_unreadable_too(
    body: bytes, content_type: str
) -> None:
    manager, _token = await _manager_over(FakeIiko(_menu(body, content_type)))

    with pytest.raises(MenuAnswerUnreadable) as error:
        await manager.get_external_menu_v3_by_id_with_answer(_request())

    assert error.value.raw == body
    assert error.value.content_type == content_type
