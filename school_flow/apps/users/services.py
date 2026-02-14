from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

from .models import Role, UserInvite, User, UserProfile, UserRole


class InviteService:
    @staticmethod
    def create_invite(
        email: str,
        role_code: str,
        profile_data: dict,
        created_by: User,
        days_valid: int = None,
    ):
        if days_valid is None:
            days_valid = settings.INVITE_EXPIRY_DAYS

        role = Role.objects.get(code=role_code)

        profile = UserProfile.objects.create(**profile_data)

        invite, _ = UserInvite.objects.update_or_create(
            email=email,
            role=role,
            defaults={
                "profile": profile,
                "expires_at": timezone.now() + timedelta(days=days_valid),
                "created_by": created_by,
            },
        )

        InviteService._send_invite_email(invite)

        return invite

    @staticmethod
    def _send_invite_email(invite: UserInvite):
        """Send invite email with registration link."""
        invite_url = f"/invites/{invite.token}/register/"

        subject = "Приглашение в систему SchoolFlow"
        message = f"""
Здравствуйте!

Вы получили приглашение в систему SchoolFlow.

Перейдите по ссылке для завершения регистрации:
{invite_url}

Ссылка действительна до: {invite.expires_at.strftime("%d.%m.%Y")}
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invite.email],
            fail_silently=False,
        )

    @staticmethod
    def validate_token(token: str) -> tuple[bool, str]:
        """
        Validate invite token.
        Returns (is_valid, error_message).
        """
        try:
            invite = UserInvite.objects.get(token=token)
        except UserInvite.DoesNotExist:
            return False, "Приглашение не найдено"

        if invite.used_at:
            return False, "Приглашение уже было использовано"

        if not invite.is_valid():
            return False, "Срок действия приглашения истек"

        return True, ""

    @staticmethod
    def extend_invite(invite: UserInvite, days: int = None):
        """Extend invite expiry date."""
        if days is None:
            days = settings.INVITE_EXPIRY_DAYS

        invite.expires_at = timezone.now() + timedelta(days=days)
        invite.save(update_fields=["expires_at", "updated_at"])
        return invite

    @staticmethod
    def complete_registration(invite: UserInvite, password: str) -> User:
        """
        Complete user registration using invite.
        Links User with UserProfile and assigns role.
        """
        user = User.objects.create_user(
            email=invite.email,
            password=password,
        )

        if invite.profile:
            invite.profile.user = user
            invite.profile.save(update_fields=["user", "updated_at"])

        UserRole.objects.create(user=user, role=invite.role)

        invite.used_at = timezone.now()
        invite.save(update_fields=["used_at", "updated_at"])

        return user
