from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from .models import User, ActivityLog, RestaurantSettings
import json


def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")
            if request.user.role not in roles and not request.user.is_superuser:
                messages.error(request, "You do not have permission to access this page.")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def log_activity(user, action, description, model_name="", object_id="", request=None):
    ip = None
    if request:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
    ActivityLog.objects.create(
        user=user, action=action, description=description,
        model_name=model_name, object_id=str(object_id) if object_id else "",
        ip_address=ip,
    )


@login_required
def profile(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.phone = request.POST.get("phone", user.phone)
        user.save()
        log_activity(user, "update", "Updated profile", "User", user.id, request)
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")
    return render(request, "accounts/profile.html")


@login_required
@role_required("owner", "manager")
def user_list(request):
    users = User.objects.all().order_by("role", "username")
    return render(request, "accounts/user_list.html", {
        "users": users,
        "role_choices": User.Role.choices,
    })


@login_required
@role_required("owner", "manager")
@require_POST
def user_update_role(request, user_id):
    target = get_object_or_404(User, id=user_id)
    new_role = request.POST.get("role")
    if new_role in dict(User.Role.choices):
        old = target.role
        target.role = new_role
        target.save(update_fields=["role"])
        log_activity(request.user, "update", f"Changed {target.username} role: {old} → {new_role}", "User", target.id, request)
        messages.success(request, f"Role updated for {target.username}.")
    return redirect("user_list")


@login_required
@role_required("owner", "manager")
def activity_logs(request):
    logs = ActivityLog.objects.select_related("user")[:100]
    return render(request, "accounts/activity_logs.html", {"logs": logs})


@login_required
@role_required("owner", "manager")
def settings_view(request):
    settings_obj = RestaurantSettings.get_solo()
    if request.method == "POST":
        settings_obj.name = request.POST.get("name", settings_obj.name)
        settings_obj.address = request.POST.get("address", settings_obj.address)
        settings_obj.phone = request.POST.get("phone", settings_obj.phone)
        settings_obj.email = request.POST.get("email", settings_obj.email)
        try:
            settings_obj.tax_rate = float(request.POST.get("tax_rate", settings_obj.tax_rate))
        except (TypeError, ValueError):
            pass
        settings_obj.currency = request.POST.get("currency", settings_obj.currency)
        settings_obj.save()
        log_activity(request.user, "update", "Updated restaurant settings", "RestaurantSettings", 1, request)
        messages.success(request, "Settings saved.")
        return redirect("settings")
    return render(request, "accounts/settings.html", {"settings": settings_obj})
