from django import forms
from django.conf import settings

from .models import UserProfile, Role, RoleCode


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Email", max_length=150, widget=forms.TextInput(attrs={"autofocus": True})
    )
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["first_name", "middle_name", "last_name", "date_of_birth", "photo"]
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "middle_name": "Отчество",
            "date_of_birth": "Дата рождения",
            "photo": "Фотография",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "middle_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "photo": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }


class InviteCreateForm(forms.Form):
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"class": "form-control"})
    )

    role = forms.ChoiceField(
        label="Роль",
        choices=[
            (RoleCode.TEACHER, "Учитель"),
            (RoleCode.STUDENT, "Ученик"),
            (RoleCode.PARENT, "Родитель"),
            (RoleCode.ADMIN, "Администратор"),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    first_name = forms.CharField(
        label="Имя",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    last_name = forms.CharField(
        label="Фамилия",
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    middle_name = forms.CharField(
        label="Отчество",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    date_of_birth = forms.DateField(
        label="Дата рождения",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    days_valid = forms.IntegerField(
        label="Срок действия (дней)",
        initial=settings.INVITE_EXPIRY_DAYS,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        from .models import UserInvite

        if UserInvite.objects.filter(email=email, used_at__isnull=True).exists():
            raise forms.ValidationError("Приглашение для этого email уже отправлено")
        from .models import User

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с этим email уже существует")
        return email


class UserRegistrationForm(forms.Form):
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password_confirm = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают")

        return cleaned_data
