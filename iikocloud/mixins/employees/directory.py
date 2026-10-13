"""Справочник сотрудников и должностей (/api/employees/v1) — прямые обёртки SDK.

Это не то же самое, что ``EmployeesCoreMixin`` (адреса ``/api/1/employees/*``: курьеры,
смены, место курьера). Здесь — карточка сотрудника целиком (с телефоном, должностями,
организациями), список сотрудников с отбором и должности.
"""

from iikocloud_client import (
    EmployeeCreateRequest,
    EmployeeFireRequest,
    EmployeeFireResponse,
    EmployeeGetRequest,
    EmployeeListRequest,
    EmployeePositionResponse,
    EmployeeResponse,
    EmployeeRestoreRequest,
    EmployeeRestoreResponse,
    EmployeeUpdateRequest,
    GetPositionRequest,
    ListPositionsRequest,
    ListPositionsResponse,
    SwaggerEmployeeListResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class EmployeesDirectoryCoreMixin(_ManagerBase):
    """Core-методы справочника сотрудников и должностей."""

    async def get_employee(self, request: EmployeeGetRequest) -> EmployeeResponse:
        """Карточка сотрудника по id (телефон, e-mail, должности, организации)."""

        async def api_call() -> EmployeeResponse:
            api = await self.get_employees_employees_api()
            return await api.get_employee(employee_get_request=request)

        return await self.execute_with_retry(ApiMethod.GET_EMPLOYEE, api_call)

    async def list_employees(
        self, request: EmployeeListRequest
    ) -> SwaggerEmployeeListResponse:
        """Страница списка сотрудников.

        Без ``fields`` iiko отдаёт только ``id``, ``name``, ``code``, ``isFired`` —
        телефон нужно запросить явно (``fields=[..., "phone"]``); см.
        ``list_all_employees``.
        """

        async def api_call() -> SwaggerEmployeeListResponse:
            api = await self.get_employees_employees_api()
            return await api.list_employees(employee_list_request=request)

        return await self.execute_with_retry(ApiMethod.LIST_EMPLOYEES, api_call)

    async def create_employee(self, request: EmployeeCreateRequest) -> EmployeeResponse:
        """Создать сотрудника (обязательны code, name, mainOrganizationId)."""

        async def api_call() -> EmployeeResponse:
            api = await self.get_employees_employees_api()
            return await api.create_employee(employee_create_request=request)

        return await self.execute_with_retry(ApiMethod.CREATE_EMPLOYEE, api_call)

    async def update_employee(self, request: EmployeeUpdateRequest) -> EmployeeResponse:
        """Изменить карточку сотрудника."""

        async def api_call() -> EmployeeResponse:
            api = await self.get_employees_employees_api()
            return await api.update_employee(employee_update_request=request)

        return await self.execute_with_retry(ApiMethod.UPDATE_EMPLOYEE, api_call)

    async def fire_employees(self, request: EmployeeFireRequest) -> EmployeeFireResponse:
        """Уволить сотрудников (список id)."""

        async def api_call() -> EmployeeFireResponse:
            api = await self.get_employees_employees_api()
            return await api.fire_employees(employee_fire_request=request)

        return await self.execute_with_retry(ApiMethod.FIRE_EMPLOYEES, api_call)

    async def restore_employee(
        self, request: EmployeeRestoreRequest
    ) -> EmployeeRestoreResponse:
        """Вернуть уволенного сотрудника."""

        async def api_call() -> EmployeeRestoreResponse:
            api = await self.get_employees_employees_api()
            return await api.restore_employee(employee_restore_request=request)

        return await self.execute_with_retry(ApiMethod.RESTORE_EMPLOYEE, api_call)

    async def get_employee_position(
        self, request: GetPositionRequest
    ) -> EmployeePositionResponse:
        """Должность по id."""

        async def api_call() -> EmployeePositionResponse:
            api = await self.get_employees_positions_api()
            return await api.get_employee_position(get_position_request=request)

        return await self.execute_with_retry(ApiMethod.GET_EMPLOYEE_POSITION, api_call)

    async def list_employee_positions(
        self, request: ListPositionsRequest
    ) -> ListPositionsResponse:
        """Страница списка должностей (по умолчанию 50, не больше 1000)."""

        async def api_call() -> ListPositionsResponse:
            api = await self.get_employees_positions_api()
            return await api.list_employee_positions(list_positions_request=request)

        return await self.execute_with_retry(ApiMethod.LIST_EMPLOYEE_POSITIONS, api_call)
