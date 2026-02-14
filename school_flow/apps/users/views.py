from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import (
    DetailView,
    UpdateView,
    ListView,
    DeleteView,
    CreateView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models

from .forms import LoginForm, UserProfileForm, InviteCreateForm, UserRegistrationForm
from .models import UserProfile, UserInvite, RoleCode, User, UserRole
from .permissions import CanViewUserProfileMixin, CanCreateUserProfileMixin
from .services import InviteService


class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(reverse_lazy("home"))
        form = LoginForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                next_url = request.GET.get("next") or reverse_lazy("home")
                return redirect(next_url)
            else:
                form.add_error(None, "Invalid username or password.")
        return render(request, self.template_name, {"form": form})


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect(reverse_lazy("home"))


class UserProfileDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = "profile_detail.html"

    def get_object(self):
        return self.request.user.profile


class UserProfileDetailByIdView(
    LoginRequiredMixin,
    CanViewUserProfileMixin,
    DetailView,
):
    model = UserProfile
    template_name = "profile_detail.html"

    def get_object(self):
        pk = self.kwargs.get("pk")
        profile = get_object_or_404(UserProfile, pk=pk)
        self.check_permissions(self.request, profile)
        return profile


@login_required
def home_view(request):
    return render(request, "home.html")


class InviteListView(LoginRequiredMixin, CanCreateUserProfileMixin, ListView):
    model = UserInvite
    template_name = "invite_list.html"
    context_object_name = "invites"
    paginate_by = 20

    def get_queryset(self):
        self.check_permissions(self.request)
        return UserInvite.objects.select_related("role", "profile").order_by(
            "-created_at"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "invites"
        return context


class InviteCreateView(LoginRequiredMixin, CanCreateUserProfileMixin, View):
    template_name = "invite_form.html"

    def get(self, request):
        self.check_permissions(request)
        form = InviteCreateForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        self.check_permissions(request)
        form = InviteCreateForm(request.POST)

        if form.is_valid():
            profile_data = {
                "first_name": form.cleaned_data["first_name"],
                "last_name": form.cleaned_data["last_name"],
                "middle_name": form.cleaned_data.get("middle_name"),
                "date_of_birth": form.cleaned_data.get("date_of_birth"),
            }

            InviteService.create_invite(
                email=form.cleaned_data["email"],
                role_code=form.cleaned_data["role"],
                profile_data=profile_data,
                created_by=request.user,
                days_valid=form.cleaned_data["days_valid"],
            )

            messages.success(
                request, f"Приглашение отправлено на {form.cleaned_data['email']}"
            )
            return redirect(reverse_lazy("users:invite_list"))

        return render(request, self.template_name, {"form": form})


class InviteRegisterView(View):
    template_name = "invite_register.html"

    def get(self, request, token):
        is_valid, error = InviteService.validate_token(token)

        if not is_valid:
            return render(request, "invite_error.html", {"error": error})

        invite = get_object_or_404(UserInvite, token=token)
        form = UserRegistrationForm()
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "invite": invite,
                "token": token,
            },
        )

    def post(self, request, token):
        is_valid, error = InviteService.validate_token(token)

        if not is_valid:
            return render(request, "invite_error.html", {"error": error})

        invite = get_object_or_404(UserInvite, token=token)
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            user = InviteService.complete_registration(
                invite=invite,
                password=form.cleaned_data["password"],
            )

            user = authenticate(
                request, username=invite.email, password=form.cleaned_data["password"]
            )
            if user:
                login(request, user)
                messages.success(request, "Регистрация успешно завершена!")
                return redirect(reverse_lazy("home"))

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "invite": invite,
                "token": token,
            },
        )


class InviteDeleteView(LoginRequiredMixin, CanCreateUserProfileMixin, DeleteView):
    model = UserInvite
    template_name = "invite_confirm_delete.html"
    success_url = reverse_lazy("users:invite_list")

    def get_object(self):
        pk = self.kwargs.get("pk")
        return get_object_or_404(UserInvite, pk=pk)

    def get(self, request, *args, **kwargs):
        self.check_permissions(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.check_permissions(request)
        invite = self.get_object()
        if invite.profile:
            invite.profile.delete()
        return super().post(request, *args, **kwargs)


class InviteExtendView(LoginRequiredMixin, CanCreateUserProfileMixin, View):
    def post(self, request, pk):
        self.check_permissions(request)
        invite = get_object_or_404(UserInvite, pk=pk)
        days = int(request.POST.get("days", 7))
        InviteService.extend_invite(invite, days)
        messages.success(request, f"Срок действия приглашения продлён")
        return redirect(reverse_lazy("users:invite_list"))


class UserProfileUpdateView(LoginRequiredMixin, CanCreateUserProfileMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "profile_form.html"
    success_url = reverse_lazy("users:invite_list")

    def get_object(self):
        pk = self.kwargs.get("pk")
        return get_object_or_404(UserProfile, pk=pk)

    def get(self, request, *args, **kwargs):
        self.check_permissions(request)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.check_permissions(request)
        return super().post(request, *args, **kwargs)


class UserListView(LoginRequiredMixin, View):
    template_name = "user_list.html"
    paginate_by = 20

    def get(self, request):
        if not request.user.is_staff:
            return redirect(reverse_lazy("home"))

        users = (
            User.objects.select_related("profile")
            .prefetch_related("roles")
            .order_by("-created_at")
        )

        q = request.GET.get("q", "").strip()
        role_filter = request.GET.get("role", "")
        status_filter = request.GET.get("status", "")

        if q:
            users = users.filter(
                models.Q(profile__first_name__icontains=q)
                | models.Q(profile__last_name__icontains=q)
            )

        if role_filter:
            users = users.filter(roles__code=role_filter)

        if status_filter == "active":
            users = users.filter(is_active=True)
        elif status_filter == "inactive":
            users = users.filter(is_active=False)

        users = users.distinct()

        paginator = Paginator(users, self.paginate_by)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context = {
            "page_obj": page_obj,
            "q": q,
            "role_filter": role_filter,
            "status_filter": status_filter,
            "roles": RoleCode.choices,
        }
        return render(request, self.template_name, context)


class UserToggleActiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return redirect(reverse_lazy("home"))

        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save(update_fields=["is_active", "updated_at"])

        status = "активирован" if user.is_active else "деактивирован"
        messages.success(request, f"Пользователь {user.email} {status}")

        return redirect(reverse_lazy("users:user_list"))
