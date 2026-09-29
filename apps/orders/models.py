from django.db import models
from django.utils import timezone
import uuid


class Table(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        RESERVED = "reserved", "Reserved"
        CLEANING = "cleaning", "Cleaning"

    number = models.CharField(max_length=10, unique=True)
    capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    location = models.CharField(max_length=50, blank=True, help_text="e.g. Indoor, Patio, VIP")
    assigned_waiter = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_tables", limit_choices_to={"role": "waiter"}
    )
    # Keep for backward compatibility
    is_occupied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Table {self.number}"

    def save(self, *args, **kwargs):
        self.is_occupied = self.status == self.Status.OCCUPIED
        super().save(*args, **kwargs)


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        SERVED = "served", "Served"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class OrderType(models.TextChoices):
        DINE_IN = "dine_in", "Dine In"
        TAKEAWAY = "takeaway", "Takeaway"
        DELIVERY = "delivery", "Delivery"

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    table = models.ForeignKey(Table, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    customer = models.ForeignKey("customers.Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DINE_IN)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, related_name="created_orders")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number: ORD-YYYYMMDD-XXXX
            date_str = timezone.now().strftime("%Y%m%d")
            unique = str(uuid.uuid4())[:4].upper()
            self.order_number = f"ORD-{date_str}-{unique}"
        super().save(*args, **kwargs)

    def calculate_totals(self):
        subtotal = sum(item.line_total for item in self.items.all())
        self.subtotal = subtotal
        self.tax = subtotal * 0.10  # 10% tax example
        self.total = self.subtotal + self.tax - self.discount
        self.save(update_fields=["subtotal", "tax", "total"])


class OrderItem(models.Model):
    class ItemStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PREPARING = "preparing", "Preparing"
        READY = "ready", "Ready"
        SERVED = "served", "Served"
        CANCELLED = "cancelled", "Cancelled"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey("menu.MenuItem", on_delete=models.PROTECT)
    variant = models.ForeignKey("menu.MenuItemVariant", null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=ItemStatus.choices, default=ItemStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    @property
    def prep_time_minutes(self):
        """Minutes from start preparing to ready."""
        if self.preparing_at and self.ready_at:
            return round((self.ready_at - self.preparing_at).total_seconds() / 60, 1)
        return None

    @property
    def service_time_minutes(self):
        """Minutes from order created to served."""
        if self.served_at:
            return round((self.served_at - self.created_at).total_seconds() / 60, 1)
        if self.order.completed_at:
            return round((self.order.completed_at - self.created_at).total_seconds() / 60, 1)
        return None
