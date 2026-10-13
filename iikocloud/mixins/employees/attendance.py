"""Явки сотрудников (/api/employees/v1/attendance) — прямые обёртки SDK.

Явка — отработанный (или назначенный) отрезок времени сотрудника в организации с типом
явки. iiko создаёт только закрытые явки: ``endAt`` обязателен (с описания 9.8.6.3).
Удаление необратимо.
"""

from iikocloud_client import (
    AttendanceCreateRequest,
    AttendanceCreateResponse,
    AttendanceDeleteRequest,
    AttendanceDeleteResponse,
    AttendanceListRequest,
    AttendanceListResponse,
    AttendanceTypeListRequest,
    AttendanceTypeListResponse,
    AttendanceUpdateRequest,
    AttendanceUpdateResponse,
)

from iikocloud.mixins._base import ApiMethod, _ManagerBase


class EmployeesAttendanceCoreMixin(_ManagerBase):
    """Core-методы явок и типов явок."""

    async def list_employee_attendances(
        self, request: AttendanceListRequest
    ) -> AttendanceListResponse:
        """Страница явок одной организации за период (не больше 1000 за раз)."""

        async def api_call() -> AttendanceListResponse:
            api = await self.get_employees_attendance_api()
            return await api.list_employee_attendances(attendance_list_request=request)

        return await self.execute_with_retry(ApiMethod.LIST_EMPLOYEE_ATTENDANCES, api_call)

    async def create_employee_attendance(
        self, request: AttendanceCreateRequest
    ) -> AttendanceCreateResponse:
        """Создать закрытую явку (открытую iiko не принимает)."""

        async def api_call() -> AttendanceCreateResponse:
            api = await self.get_employees_attendance_api()
            return await api.create_employee_attendance(attendance_create_request=request)

        return await self.execute_with_retry(ApiMethod.CREATE_EMPLOYEE_ATTENDANCE, api_call)

    async def update_employee_attendance(
        self, request: AttendanceUpdateRequest
    ) -> AttendanceUpdateResponse:
        """Изменить явку; смена организации даёт новую явку с новым id."""

        async def api_call() -> AttendanceUpdateResponse:
            api = await self.get_employees_attendance_api()
            return await api.update_employee_attendance(attendance_update_request=request)

        return await self.execute_with_retry(ApiMethod.UPDATE_EMPLOYEE_ATTENDANCE, api_call)

    async def delete_employee_attendance(
        self, request: AttendanceDeleteRequest
    ) -> AttendanceDeleteResponse:
        """Удалить одну явку (необратимо)."""

        async def api_call() -> AttendanceDeleteResponse:
            api = await self.get_employees_attendance_api()
            return await api.delete_employee_attendance(attendance_delete_request=request)

        return await self.execute_with_retry(ApiMethod.DELETE_EMPLOYEE_ATTENDANCE, api_call)

    async def list_employee_attendance_types(
        self, request: AttendanceTypeListRequest
    ) -> AttendanceTypeListResponse:
        """Справочник типов явок (явка, больничный, отпуск …; ``isPresence``)."""

        async def api_call() -> AttendanceTypeListResponse:
            api = await self.get_employees_attendance_api()
            return await api.list_employee_attendance_types(
                attendance_type_list_request=request
            )

        return await self.execute_with_retry(
            ApiMethod.LIST_EMPLOYEE_ATTENDANCE_TYPES, api_call
        )
