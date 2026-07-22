"""Organizations helpers mixin — convenience-методы через core."""

from iikocloud.mixins.organizations.core import OrganizationsCoreMixin


class OrganizationsHelpersMixin(OrganizationsCoreMixin):
    """Публичный organizations mixin (core уже задаёт default empty request)."""
