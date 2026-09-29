from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "loyalty_points", "total_spent", "visit_count"]
    search_fields = ["name", "phone"]
