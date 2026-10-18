from django.contrib import admin
from django.utils.html import format_html
from .models import Category, MenuItem, MenuItemVariant


class MenuItemVariantInline(admin.TabularInline):
    model = MenuItemVariant
    extra = 1
    ordering = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "sort_order", "items_count"]
    list_editable = ["is_active", "sort_order"]
    search_fields = ["name"]
    prepopulated_fields = {}

    @admin.display(description="Items")
    def items_count(self, obj):
        return obj.items.count()


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["thumbnail", "name", "category", "price", "portion_size", "available_quantity", "is_available", "is_featured", "spice_level", "variants_count"]
    list_display_links = ["name"]
    list_filter = ["category", "is_available", "is_featured", "is_vegetarian", "is_vegan", "is_gluten_free", "spice_level"]
    search_fields = ["name", "description", "allergens"]
    list_editable = ["is_available", "is_featured", "price"]

    @admin.display(description="Variants")
    def variants_count(self, obj):
        return obj.variants.count()
    inlines = [MenuItemVariantInline]
    readonly_fields = ["created_at", "updated_at", "image_preview"]
    fieldsets = (
        ("Core", {"fields": ("name", "category", "description", "price", "portion_size")}),
        ("Image", {"fields": ("image", "image_preview")}),
        ("Availability", {"fields": ("is_available", "is_featured", "available_quantity", "preparation_time", "calories")}),
        ("Dietary & allergens", {"fields": ("is_vegetarian", "is_vegan", "is_gluten_free", "spice_level", "allergens")}),
        ("Meta", {"fields": ("sku", "created_at", "updated_at")}),
    )

    @admin.display(description="Photo")
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:8px;" />', obj.image.url)
        return "—"

    @admin.display(description="Image preview")
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:240px;border-radius:12px;" />', obj.image.url)
        return "No image uploaded."