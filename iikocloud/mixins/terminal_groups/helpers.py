"""Terminal groups helpers mixin — convenience-методы через core."""

from uuid import UUID

from iikocloud_client import TerminalGroupsRequest, TerminalGroupsResponse

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.terminal_groups.core import TerminalGroupsCoreMixin


class TerminalGroupsHelpersMixin(TerminalGroupsCoreMixin):
    """Публичный terminal groups mixin с convenience-методами."""

    async def get_terminal_groups_by_organization(
        self,
        organization_id: str | UUID,
    ) -> TerminalGroupsResponse:
        """Получить терминальные группы для организации.

        Args:
            organization_id: ID организации (str или UUID)

        Returns:
            Ответ со списком терминальных групп
        """
        request = TerminalGroupsRequest(
            organization_ids=[as_uuid(organization_id)],
        )
        return await self.get_terminal_groups(request)
