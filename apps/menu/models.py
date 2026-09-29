from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Emoji or icon class")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="menu_items/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    preparation_time = models.PositiveIntegerField(help_text="Minutes", default=15)
    calories = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class MenuItemVariant(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=100)  # e.g. "Large", "Extra Cheese"
    price_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.menu_item.name} - {self.name}"
