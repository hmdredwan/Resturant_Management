from django.contrib import admin
from .models import Category, MenuItem, MenuItemVariant

class MenuItemVariantInline(admin.TabularInline):
    model = MenuItemVariant
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "is_available", "is_featured"]
    list_filter = ["category", "is_available", "is_featured"]
    search_fields = ["name"]
    inlines = [MenuItemVariantInline]
