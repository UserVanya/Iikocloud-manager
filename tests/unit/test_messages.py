"""Unit tests for Messages domain mixins."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from iikocloud_client import (
    CheckSmsStatusRequest,
    CheckSmsStatusResponse,
    SendEmailRequest,
    SendSmsRequest,
    SendSmsResponse,
    SmsSendingPossibilityRequest,
    SmsSendingPossibilityResponse,
)

from tests.unit.conftest import manager_with_stub_api

pytestmark = pytest.mark.unit

ORG_ID = UUID("12345678-1234-1234-1234-123456789abc")
API_SLOT = "_messages_api"

METHODS: list[tuple[str, object, str, type]] = [
    (
        "check_sms_sending_possibility",
        SmsSendingPossibilityRequest(organization_id=ORG_ID),
        "sms_sending_possibility_request",
        SmsSendingPossibilityResponse,
    ),
    (
        "check_sms_status",
        CheckSmsStatusRequest(organization_id=ORG_ID, sms_ids=[ORG_ID]),
        "check_sms_status_request",
        CheckSmsStatusResponse,
    ),
    (
        "send_loyalty_sms",
        SendSmsRequest(organization_id=ORG_ID, phone="+79990001122", text="t"),
        "send_sms_request",
        SendSmsResponse,
    ),
]


@pytest.mark.parametrize(
    ("method_name", "sdk_request", "sdk_kwarg", "response_cls"), METHODS
)
async def test_messages_methods_delegate(
    method_name: str, sdk_request: object, sdk_kwarg: str, response_cls: type
) -> None:
    """check-методы и send_sms проксируют response."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_response = MagicMock(spec=response_cls)
    sdk_method = AsyncMock(return_value=mock_response)
    setattr(mock_api, method_name, sdk_method)

    result = await getattr(manager, method_name)(sdk_request)

    assert result is mock_response
    sdk_method.assert_awaited_once_with(**{sdk_kwarg: sdk_request})


async def test_send_loyalty_email_returns_none() -> None:
    """send_loyalty_email: object-ответ -> None."""
    manager, mock_api = await manager_with_stub_api(API_SLOT)
    mock_api.send_loyalty_email = AsyncMock(return_value={})

    request = SendEmailRequest(
        organization_id=ORG_ID, receiver="a@b.c", subject="s", body="b"
    )
    result = await manager.send_loyalty_email(request)

    assert result is None
    mock_api.send_loyalty_email.assert_awaited_once_with(
        send_email_request=request
    )
