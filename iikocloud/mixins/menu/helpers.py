"""Menu helpers mixin — convenience-методы через core."""

from uuid import UUID

from iikocloud_client import StopListsRequest, StopListsResponse

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.menu.core import MenuCoreMixin


class MenuHelpersMixin(MenuCoreMixin):
    """Публичный menu mixin с convenience-методами."""

    async def get_stop_lists_by_organization(
        self,
        organization_id: str | UUID,
    ) -> StopListsResponse:
        """Получить стоп-листы для организации.

        Args:
            organization_id: ID организации (str или UUID)

        Returns:
            Ответ со стоп-листами организации
        """
        request = StopListsRequest(
            organization_ids=[as_uuid(organization_id)],
        )
        return await self.get_stop_lists(request)
