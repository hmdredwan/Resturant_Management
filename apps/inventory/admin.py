from django.contrib import admin
from .models import Ingredient, Recipe, RecipeIngredient

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 2

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name", "current_stock", "unit", "minimum_stock", "is_low_stock"]
    list_filter = ["unit"]
    search_fields = ["name"]

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]

from .models import StockAdjustment

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ["ingredient", "quantity_change", "reason", "adjusted_by", "created_at"]
    list_filter = ["reason"]
