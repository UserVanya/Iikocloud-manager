"""Employees core mixin — прямые обёртки SDK через execute_with_retry."""

from iikocloud_client import (
    ActiveCourierLocationsByTerminalGroupRequest,
    ActiveCourierLocationsResponse,
    ChangePersonalSessionResponse,
    ClosePersonalSessionRequest,
    CourierLocationsByTimeOffsetRequest,
    CourierLocationsByTimeOffsetResponse,
    CouriersAndCheckRoleRequest,
    CouriersRequest,
    EmployeeInfoRequest,
    EmployeeInfoResponse,
    EmployeesResponse,
    EmployeesWithRoleSignResponse,
    GetPersonalSessionInfoRequest,
    GetPersonalSessionInfoResponse,
    GetTerminalGroupsOfEmployeeRequest,
    GetTerminalGroupsOfEmployeeResponse,
    OpenPersonalSessionRequest,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class EmployeesCoreMixin(_ManagerBase):
    """Core-методы Employees API (курьеры, сессии, информация о сотрудниках)."""

    async def get_couriers(self, request: CouriersRequest) -> EmployeesResponse:
        """Сотрудники-курьеры организаций."""

        async def api_call() -> EmployeesResponse:
            api = await self.get_employees_api()
            return await api.get_couriers(couriers_request=request)

        return await self.execute_with_retry(ApiMethod.GET_COURIERS, api_call)

    async def get_couriers_by_role(
        self, request: CouriersAndCheckRoleRequest
    ) -> EmployeesWithRoleSignResponse:
        """Курьеры с проверкой ролей."""

        async def api_call() -> EmployeesWithRoleSignResponse:
            api = await self.get_employees_api()
            return await api.get_couriers_by_role(
                couriers_and_check_role_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_COURIERS_BY_ROLE, api_call
        )

    async def get_employee_info(
        self, request: EmployeeInfoRequest
    ) -> EmployeeInfoResponse:
        """Информация о сотруднике по id."""

        async def api_call() -> EmployeeInfoResponse:
            api = await self.get_employees_api()
            return await api.get_employee_info(employee_info_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_EMPLOYEE_INFO, api_call
        )

    async def get_active_courier_locations(
        self, request: CouriersRequest
    ) -> ActiveCourierLocationsResponse:
        """Локации активных курьеров."""

        async def api_call() -> ActiveCourierLocationsResponse:
            api = await self.get_employees_api()
            return await api.get_active_courier_locations(couriers_request=request)

        return await self.execute_with_retry(
            ApiMethod.GET_ACTIVE_COURIER_LOCATIONS, api_call
        )

    async def get_active_courier_locations_by_terminal(
        self, request: ActiveCourierLocationsByTerminalGroupRequest
    ) -> ActiveCourierLocationsResponse:
        """Локации курьеров терминала."""

        async def api_call() -> ActiveCourierLocationsResponse:
            api = await self.get_employees_api()
            return await api.get_active_courier_locations_by_terminal(
                active_courier_locations_by_terminal_group_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_ACTIVE_COURIER_LOCATIONS_BY_TERMINAL, api_call
        )

    async def get_courier_location_history(
        self, request: CourierLocationsByTimeOffsetRequest
    ) -> CourierLocationsByTimeOffsetResponse:
        """История координат курьеров (offset в секундах)."""

        async def api_call() -> CourierLocationsByTimeOffsetResponse:
            api = await self.get_employees_api()
            return await api.get_courier_location_history(
                courier_locations_by_time_offset_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_COURIER_LOCATION_HISTORY, api_call
        )

    async def get_personal_session_info(
        self, request: GetPersonalSessionInfoRequest
    ) -> GetPersonalSessionInfoResponse:
        """Открыта ли личная сессия сотрудника."""

        async def api_call() -> GetPersonalSessionInfoResponse:
            api = await self.get_employees_api()
            return await api.get_personal_session_info(
                get_personal_session_info_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_PERSONAL_SESSION_INFO, api_call
        )

    async def get_terminal_groups_of_employee(
        self, request: GetTerminalGroupsOfEmployeeRequest
    ) -> GetTerminalGroupsOfEmployeeResponse:
        """Терминальные группы с открытой сессией сотрудника."""

        async def api_call() -> GetTerminalGroupsOfEmployeeResponse:
            api = await self.get_employees_api()
            return await api.get_terminal_groups_of_employee(
                get_terminal_groups_of_employee_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.GET_TERMINAL_GROUPS_OF_EMPLOYEE, api_call
        )

    async def open_personal_session(
        self, request: OpenPersonalSessionRequest
    ) -> ChangePersonalSessionResponse:
        """Открыть смену (команда; role_id — только если ресторан использует роли)."""

        async def api_call() -> ChangePersonalSessionResponse:
            api = await self.get_employees_api()
            return await api.open_personal_session(
                open_personal_session_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.OPEN_PERSONAL_SESSION, api_call
        )

    async def close_personal_session(
        self, request: ClosePersonalSessionRequest
    ) -> ChangePersonalSessionResponse:
        """Закрыть смену (команда)."""

        async def api_call() -> ChangePersonalSessionResponse:
            api = await self.get_employees_api()
            return await api.close_personal_session(
                close_personal_session_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.CLOSE_PERSONAL_SESSION, api_call
        )
