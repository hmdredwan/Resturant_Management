from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        MANAGER = "manager", "Manager"
        CASHIER = "cashier", "Cashier"
        WAITER = "waiter", "Waiter"
        KITCHEN = "kitchen", "Kitchen Staff"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WAITER)
    phone = models.CharField(max_length=20, blank=True)
    is_active_staff = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_manager_or_owner(self):
        return self.role in [self.Role.OWNER, self.Role.MANAGER]

    def has_perm_action(self, action):
        """Simple RBAC helper: action in view, create, edit, delete, approve"""
        perms = {
            "owner": {"view", "create", "edit", "delete", "approve"},
            "manager": {"view", "create", "edit", "delete", "approve"},
            "cashier": {"view", "create", "edit"},
            "waiter": {"view", "create", "edit"},
            "kitchen": {"view", "edit"},
        }
        return action in perms.get(self.role, set())


class ActivityLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        STATUS_CHANGE = "status_change", "Status Change"
        STOCK_ADJUST = "stock_adjust", "Stock Adjustment"
        OTHER = "other", "Other"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_logs")
    action = models.CharField(max_length=20, choices=Action.choices, default=Action.OTHER)
    model_name = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.action} — {self.created_at:%Y-%m-%d %H:%M}"


class RestaurantSettings(models.Model):
    """Singleton-style settings for the restaurant."""
    name = models.CharField(max_length=150, default="My Restaurant")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Tax percentage")
    currency = models.CharField(max_length=10, default="USD")
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    logo = models.ImageField(upload_to="restaurant/", blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Restaurant Settings"

    def __str__(self):
        return self.name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
