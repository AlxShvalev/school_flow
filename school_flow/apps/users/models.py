import uuid
from django.utils import timezone

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager
from apps.core.models import BaseModel


class RoleCode(models.TextChoices):
    NONE = "NONE", "None"
    ADMIN = "ADMIN", "Administrator"
    TEACHER = "TEACHER", "Teacher"
    STUDENT = "STUDENT", "Student"
    PARENT = "PARENT", "Parent"


class Role(BaseModel):
    """
    Describes a user role in system.
    """

    class Meta:
        verbose_name = "role"
        verbose_name_plural = "roles"

    code = models.CharField(
        unique=True,
        max_length=10,
        choices=RoleCode.choices,
        default=RoleCode.NONE,
    )

    users = models.ManyToManyField("User", through="UserRole", related_name="roles")

    def __str__(self):
        return str(self.get_code_display())


class UserRole(BaseModel):
    """
    Links UserProfile and Role models.
    """

    user = models.ForeignKey("User", on_delete=models.CASCADE)
    role = models.ForeignKey("Role", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "role")

    def __str__(self):
        return f"{self.user} - {self.role}"


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """
    Base model for user authentication and authorization.
    """

    email = models.EmailField(unique=True)
    username = None
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    USERNAME_FIELD = "email"
    objects = UserManager()

    REQUIRED_FIELDS = []

    def has_role(self, role_code: RoleCode) -> bool:
        """
        Checks if the user has a specific role.
        :param role_code: Role code to check.
        :return: True if the user has the role, False otherwise.
        """
        return self.roles.filter(code=role_code).exists()

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email


class UserProfile(BaseModel):
    """
    Describes a user profile. It may exist without a User model, but one can be added later.
    For example, a student may exist in the system for business processes
    but not have an account to log in and view their schedule and grades.
     Afterward, they can obtain an account and view their schedule and grades.
    """

    user = models.OneToOneField(
        "User", on_delete=models.SET_NULL, null=True, blank=True, related_name="profile"
    )
    first_name = models.CharField(max_length=30)
    middle_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="media/profiles/", null=True, blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "profile"
        verbose_name_plural = "profiles"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class UserInvite(BaseModel):
    """
    User invitation model. Includes existing user profile and user role.
    """

    email = models.EmailField(unique=True)
    profile = models.ForeignKey(
        "UserProfile", on_delete=models.SET_NULL, null=True, blank=True
    )
    role = models.ForeignKey("Role", on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    token = models.UUIDField(default=uuid.uuid4, unique=True)

    used_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_invites",
    )

    class Meta:
        verbose_name = "invite"
        verbose_name_plural = "invites"

    def is_valid(self) -> bool:
        """Check if invite is valid (not expired and not used)."""
        return not self.used_at and self.expires_at and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.email} - {self.role}"
