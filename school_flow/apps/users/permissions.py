from django.core.exceptions import PermissionDenied
from .models import RoleCode


class CanViewUserProfileMixin:
    """
    Разрешает просмотр профиля пользователя:
    - просмотр своего профиля
    - администратору
    - учителю
    TODO: добавить разрешение на просмотр профиля для родителей (только своих детей)
    """

    def has_permission(self, request, profile) -> bool:
        user = request.user

        if not user.is_authenticated:
            return False

        if profile.user == user:
            return True

        if user.has_role(RoleCode.ADMIN):
            return True

        if user.has_role(RoleCode.TEACHER):
            return True

        if user.is_superuser or user.is_staff:
            return True

        return False

    def check_permissions(self, request, profile):
        if not self.has_permission(request, profile):
            raise PermissionDenied


class CanCreateUserProfileMixin:
    """
    Разрешает создание профиля:
    - администратору
    - пользователям с правами суперпользователя или персонала
    """

    def has_permission(self, request) -> bool:
        user = request.user

        if not user.is_authenticated:
            return False

        if user.has_role(RoleCode.ADMIN):
            return True

        if user.is_superuser or user.is_staff:
            return True

        return False

    def check_permissions(self, request):
        if not self.has_permission(request):
            raise PermissionDenied
