"""Operations helpers mixin — polling статусов команд."""

import asyncio
import time
from uuid import UUID

from iikocloud_client import (
    ErrorCommandStatus,
    GetCommandStatusRequest,
    SuccessCommandStatus,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.operations.core import OperationsCoreMixin

_TERMINAL = (SuccessCommandStatus, ErrorCommandStatus)


class OperationsHelpersMixin(OperationsCoreMixin):
    """Публичный operations mixin с polling-helpers."""

    async def wait_command(
        self,
        correlation_id: str | UUID,
        organization_id: str | UUID,
        *,
        timeout: float = 30.0,
        interval: float = 2.0,
    ) -> SuccessCommandStatus | ErrorCommandStatus:
        """Дождаться терминального статуса команды (Success/Error).

        Raises:
            TimeoutError: статус не стал терминальным за timeout
        """
        request = GetCommandStatusRequest(
            organization_id=as_uuid(organization_id),
            correlation_id=as_uuid(correlation_id),
        )
        deadline = time.monotonic() + timeout
        last_state = "unknown"
        while True:
            status = await self.get_command_status(request)
            if isinstance(status, _TERMINAL):
                return status
            last_state = getattr(status, "state", last_state)
            if time.monotonic() + interval > deadline:
                raise TimeoutError(
                    f"wait_command: за {timeout}s статус остался {last_state}"
                )
            await asyncio.sleep(interval)
