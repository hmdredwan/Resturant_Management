from django.db import models
from django.db.models import F


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, help_text="kg, liter, pcs, etc.")
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier = models.CharField(max_length=150, blank=True)
    last_restocked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.unit})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock


class Recipe(models.Model):
    menu_item = models.OneToOneField("menu.MenuItem", on_delete=models.CASCADE, related_name="recipe")
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recipe for {self.menu_item.name}"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ["recipe", "ingredient"]

    def __str__(self):
        return f"{self.quantity} {self.ingredient.unit} of {self.ingredient.name}"


class StockAdjustment(models.Model):
    class Reason(models.TextChoices):
        PURCHASE = "purchase", "Purchase / Restock"
        CONSUMPTION = "consumption", "Consumption"
        WASTE = "waste", "Waste / Spoilage"
        CORRECTION = "correction", "Manual Correction"
        RETURN = "return", "Return to Supplier"

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="adjustments")
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2, help_text="Positive = add, Negative = remove")
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.CORRECTION)
    notes = models.CharField(max_length=255, blank=True)
    adjusted_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        sign = "+" if self.quantity_change >= 0 else ""
        return f"{self.ingredient.name}: {sign}{self.quantity_change} ({self.reason})"
