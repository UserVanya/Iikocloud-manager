"""Employees domain mixins."""

from iikocloud.mixins.employees.attendance import EmployeesAttendanceCoreMixin
from iikocloud.mixins.employees.core import EmployeesCoreMixin
from iikocloud.mixins.employees.directory import EmployeesDirectoryCoreMixin
from iikocloud.mixins.employees.helpers import (
    EMPLOYEE_CONTACT_FIELDS,
    EmployeesHelpersMixin,
)

__all__ = [
    "EMPLOYEE_CONTACT_FIELDS",
    "EmployeesAttendanceCoreMixin",
    "EmployeesCoreMixin",
    "EmployeesDirectoryCoreMixin",
    "EmployeesHelpersMixin",
]
