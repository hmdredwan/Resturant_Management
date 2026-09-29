from django.contrib import admin
from .models import Table, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ["number", "capacity", "is_occupied", "location"]
    list_editable = ["is_occupied"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "order_type", "status", "table", "total", "created_at"]
    list_filter = ["status", "order_type"]
    search_fields = ["order_number"]
    inlines = [OrderItemInline]
