from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    visit_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def add_points(self, amount):
        """Add loyalty points (1 point per $1 spent for example)"""
        points = int(amount)
        self.loyalty_points += points
        self.total_spent += amount
        self.visit_count += 1
        self.save(update_fields=["loyalty_points", "total_spent", "visit_count"])
