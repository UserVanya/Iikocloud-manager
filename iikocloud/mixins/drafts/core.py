"""Drafts core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    CommitDraftRequest,
    CorrelationIdResponse,
    CreateDraftRequest,
    CreateOrSaveDraftResponse,
    DeleteDraftRequest,
    FilterDraftsRequest,
    FilterDraftsResponse,
    GetDraftRequest,
    GetDraftResponse,
    LockOrUnlockDraftRequest,
    OrderResponse,
    SaveDraftRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class DraftsCoreMixin(_ManagerBase):
    """Core-методы Drafts API (черновики заказов доставки)."""

    async def create_delivery_draft(
        self,
        request: CreateDraftRequest,
    ) -> CreateOrSaveDraftResponse:
        """Создать черновик заказа (order обязателен: menu_id, phone, items)."""

        async def api_call() -> CreateOrSaveDraftResponse:
            api = await self.get_drafts_api()
            return await api.create_delivery_draft(create_draft_request=request)

        return await self.execute_with_retry(
            ApiMethod.CREATE_DELIVERY_DRAFT, api_call
        )

    async def save_delivery_draft(
        self,
        request: SaveDraftRequest,
    ) -> CreateOrSaveDraftResponse:
        """Обновить существующий черновик (order.id цели + employee_id)."""

        async def api_call() -> CreateOrSaveDraftResponse:
            api = await self.get_drafts_api()
            return await api.save_delivery_draft(save_draft_request=request)

        return await self.execute_with_retry(
            ApiMethod.SAVE_DELIVERY_DRAFT, api_call
        )

    async def commit_delivery_draft(
        self,
        request: CommitDraftRequest,
    ) -> OrderResponse:
        """Финализировать черновик в заказ во Front (≈ создание заказа)."""

        async def api_call() -> OrderResponse:
            api = await self.get_drafts_api()
            return await api.commit_delivery_draft(commit_draft_request=request)

        return await self.execute_with_retry(
            ApiMethod.COMMIT_DELIVERY_DRAFT, api_call
        )

    async def delete_delivery_draft(
        self,
        request: DeleteDraftRequest,
    ) -> CorrelationIdResponse:
        """Удалить черновик."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_drafts_api()
            return await api.delete_delivery_draft(delete_draft_request=request)

        return await self.execute_with_retry(
            ApiMethod.DELETE_DELIVERY_DRAFT, api_call
        )

    async def lock_delivery_draft(
        self,
        request: LockOrUnlockDraftRequest,
    ) -> CorrelationIdResponse:
        """Заблокировать черновик (employee_id)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_drafts_api()
            return await api.lock_delivery_draft(
                lock_or_unlock_draft_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LOCK_DELIVERY_DRAFT, api_call
        )

    async def unlock_delivery_draft(
        self,
        request: LockOrUnlockDraftRequest,
    ) -> CorrelationIdResponse:
        """Разблокировать черновик (employee_id)."""

        async def api_call() -> CorrelationIdResponse:
            api = await self.get_drafts_api()
            return await api.unlock_delivery_draft(
                lock_or_unlock_draft_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.UNLOCK_DELIVERY_DRAFT, api_call
        )

    async def get_delivery_draft_by_id(
        self,
        request: GetDraftRequest,
    ) -> GetDraftResponse:
        """Черновик по id."""

        async def api_call() -> GetDraftResponse:
            api = await self.get_drafts_api()
            return await api.get_delivery_draft_by_id(get_draft_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERY_DRAFT_BY_ID, api_call
        )

    async def get_delivery_drafts_by_filter(
        self,
        request: FilterDraftsRequest,
    ) -> FilterDraftsResponse:
        """Черновики по фильтру (phone, даты, offset/limit-пагинация)."""

        async def api_call() -> FilterDraftsResponse:
            api = await self.get_drafts_api()
            return await api.get_delivery_drafts_by_filter(
                filter_drafts_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_DELIVERY_DRAFTS_BY_FILTER, api_call
        )
