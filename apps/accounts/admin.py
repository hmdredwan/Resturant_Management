from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "role", "is_active_staff", "is_staff"]
    list_filter = ["role", "is_active_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Restaurant Info", {"fields": ("role", "phone", "is_active_staff", "avatar")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Restaurant Info", {"fields": ("role", "phone")}),
    )

from .models import ActivityLog, RestaurantSettings

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "user", "action", "description"]
    list_filter = ["action"]
    readonly_fields = ["user", "action", "model_name", "object_id", "description", "ip_address", "created_at"]

@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = ["name", "tax_rate", "currency", "updated_at"]
