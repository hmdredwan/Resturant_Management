from django.contrib import admin
from .models import Shift

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ["staff", "start_time", "end_time", "is_completed"]
    list_filter = ["is_completed"]
