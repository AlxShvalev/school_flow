from django.contrib import admin

from .models import Role, User, UserInvite, UserRole, UserProfile


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1


class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = True
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    model = User
    inlines = (UserRoleInline, ProfileInline)
    list_display = (
        'email',
        'is_staff',
        'is_active',
    )
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    model = Role
    list_display = ('code',)
    search_fields = ('code',)
    ordering = ('code',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    model = UserRole
    list_display = ('user', 'role')
    search_fields = ('user__email', 'role__name')
    ordering = ('user__email',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    model = UserProfile
    list_display = (
        'first_name',
        'middle_name',
        'last_name',
        'date_of_birth',
    )
    search_fields = ('last_name', 'user__email')
    ordering = ('last_name', 'first_name')


@admin.register(UserInvite)
class UserInviteAdmin(admin.ModelAdmin):
    model = UserInvite
    list_display = ('email', 'role', 'expires_at', 'used_at')
    search_fields = ('email', 'role__name')
    ordering = ('email',)