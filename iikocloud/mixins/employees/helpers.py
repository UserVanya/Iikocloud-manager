"""Employees helpers mixin — convenience-методы поверх core-методов раздела.

Раздел сотрудников собран из трёх core-миксинов:

- ``EmployeesCoreMixin`` — адреса ``/api/1/employees/*``: курьеры (в т. ч. с проверкой
  ролей), карточка по id, личная смена (открыть, закрыть, открыта ли, где открыта),
  места курьеров;
- ``EmployeesDirectoryCoreMixin`` — справочник ``/api/employees/v1``: сотрудники
  (карточка, список, создать, изменить, уволить, вернуть) и должности;
- ``EmployeesAttendanceCoreMixin`` — явки и типы явок.

Расписания (графика смен) в облачном API iiko нет — только явки.
"""

from collections.abc import Sequence
from uuid import UUID

from iikocloud_client import (
    AttendanceListRequest,
    AttendanceResponse,
    CouriersRequest,
    EmployeeDirectoryEntry,
    EmployeeListRequest,
    EmployeeResponse,
    EmployeesFilter,
    GetPersonalSessionInfoRequest,
)

from iikocloud.mixins._base import as_uuid
from iikocloud.mixins.employees.attendance import EmployeesAttendanceCoreMixin
from iikocloud.mixins.employees.core import EmployeesCoreMixin
from iikocloud.mixins.employees.directory import EmployeesDirectoryCoreMixin

# Поля карточки, которые ``list_all_employees`` просит по умолчанию. Без ``fields`` iiko
# отдаёт только id, name, code, isFired — без телефона.
EMPLOYEE_CONTACT_FIELDS: tuple[str, ...] = (
    "id",
    "code",
    "name",
    "firstName",
    "lastName",
    "middleName",
    "phone",
    "email",
    "isFired",
    "mainRoleId",
    "roleIds",
    "mainOrganizationId",
    "organizationIds",
)

# Успех iiko пишет в поле ошибки словами (стенд, 13.10.2026: ``error: "NO_ERROR"``).
_NO_ERROR = frozenset({"", "NO_ERROR"})

# Предохранитель постраничного обхода: столько страниц подряд — уже ошибка, а не данные.
_MAX_PAGES = 1000


class EmployeesHelpersMixin(
    EmployeesCoreMixin, EmployeesDirectoryCoreMixin, EmployeesAttendanceCoreMixin
):
    """Публичный employees mixin: core-методы трёх частей раздела и помощники."""

    async def list_organization_couriers(
        self, organization_id: str | UUID
    ) -> list[EmployeeDirectoryEntry]:
        """Курьеры одной организации плоским списком (``/api/1/employees/couriers``)."""
        response = await self.get_couriers(
            CouriersRequest(organization_ids=[as_uuid(organization_id)])
        )
        return [item for group in response.employees for item in group.items]

    async def is_personal_session_open(
        self,
        employee_id: str | UUID,
        organization_id: str | UUID,
        terminal_group_id: str | UUID,
    ) -> bool:
        """Открыта ли личная смена сотрудника на терминальной группе (только чтение).

        Raises:
            RuntimeError: iiko ответил ошибкой в теле (``error`` — не пусто и не
                ``NO_ERROR``) вместо признака смены.
        """
        response = await self.get_personal_session_info(
            GetPersonalSessionInfoRequest(
                employee_id=as_uuid(employee_id),
                organization_id=as_uuid(organization_id),
                terminal_group_id=as_uuid(terminal_group_id),
            )
        )
        if (response.error or "") not in _NO_ERROR:
            raise RuntimeError(f"iiko не ответил, открыта ли смена: {response.error}")
        return bool(response.is_session_opened)

    async def list_all_employees(
        self,
        *,
        filters: Sequence[EmployeesFilter] = (),
        fields: Sequence[str] = EMPLOYEE_CONTACT_FIELDS,
        page_size: int = 500,
    ) -> list[EmployeeResponse]:
        """Все сотрудники по отбору — постранично, с телефоном по умолчанию.

        Args:
            filters: условия отбора iiko (поле и значение; все сразу, через «и»), например
                ``EmployeesFilter(var_field="isFired", value="false")``.
            fields: какие поля карточки вернуть (по умолчанию ``EMPLOYEE_CONTACT_FIELDS``,
                с ``phone``).
            page_size: сколько сотрудников в одном запросе.
        """
        if page_size < 1:
            raise ValueError("page_size должен быть >= 1")
        employees: list[EmployeeResponse] = []
        for page in range(_MAX_PAGES):
            response = await self.list_employees(
                EmployeeListRequest(
                    fields=list(fields),
                    filters=list(filters),
                    limit=page_size,
                    offset=page * page_size,
                )
            )
            items = response.items or []
            employees.extend(items)
            total = response.total_count
            if len(items) < page_size or (total is not None and len(employees) >= total):
                return employees
        raise RuntimeError(f"Список сотрудников длиннее {_MAX_PAGES} страниц")

    async def list_all_employee_attendances(
        self,
        organization_id: str | UUID,
        start_at: str,
        end_at: str,
        *,
        employee_ids: Sequence[str | UUID] | None = None,
        is_closed: bool | None = None,
        page_size: int = 1000,
    ) -> list[AttendanceResponse]:
        """Все явки организации за период — постранично (iiko отдаёт до 1000 за раз).

        Args:
            organization_id: организация.
            start_at: начало периода — дата и время в том виде, как принимает iiko.
            end_at: конец периода.
            employee_ids: только явки этих сотрудников.
            is_closed: ``True`` — только закрытые, ``False`` — только открытые,
                ``None`` — все.
            page_size: сколько явок в одном запросе (1..1000).
        """
        if not 1 <= page_size <= 1000:
            raise ValueError("page_size должен быть от 1 до 1000")
        attendances: list[AttendanceResponse] = []
        for page in range(_MAX_PAGES):
            response = await self.list_employee_attendances(
                AttendanceListRequest(
                    organization_id=as_uuid(organization_id),
                    start_at=start_at,
                    end_at=end_at,
                    employee_ids=(
                        [as_uuid(e) for e in employee_ids] if employee_ids else None
                    ),
                    is_closed=is_closed,
                    limit=page_size,
                    offset=page * page_size,
                )
            )
            items = response.items or []
            attendances.extend(items)
            total = response.total_count
            if len(items) < page_size or (total is not None and len(attendances) >= total):
                return attendances
        raise RuntimeError(f"Список явок длиннее {_MAX_PAGES} страниц")
