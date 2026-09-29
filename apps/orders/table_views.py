from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Table
from apps.accounts.models import User
from apps.accounts.views import log_activity, role_required
import json


@login_required
def table_list(request):
    tables = Table.objects.select_related("assigned_waiter").all()
    waiters = User.objects.filter(role="waiter", is_active_staff=True)
    return render(request, "orders/tables.html", {
        "tables": tables,
        "waiters": waiters,
        "status_choices": Table.Status.choices,
    })


@login_required
@role_required("owner", "manager", "cashier")
@require_POST
def table_create(request):
    number = request.POST.get("number", "").strip()
    capacity = request.POST.get("capacity", 4)
    location = request.POST.get("location", "")
    if not number:
        messages.error(request, "Table number is required.")
        return redirect("table_list")
    if Table.objects.filter(number=number).exists():
        messages.error(request, f"Table {number} already exists.")
        return redirect("table_list")
    table = Table.objects.create(number=number, capacity=capacity, location=location)
    log_activity(request.user, "create", f"Created table {number}", "Table", table.id, request)
    messages.success(request, f"Table {number} created.")
    return redirect("table_list")


@login_required
@require_POST
def table_update_status(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    try:
        data = json.loads(request.body) if request.content_type == "application/json" else request.POST
    except json.JSONDecodeError:
        data = request.POST
    new_status = data.get("status")
    if new_status in dict(Table.Status.choices):
        old = table.status
        table.status = new_status
        table.save()
        log_activity(request.user, "status_change", f"Table {table.number}: {old} → {new_status}", "Table", table.id, request)
        return JsonResponse({"success": True, "status": table.status, "status_display": table.get_status_display()})
    return JsonResponse({"success": False, "error": "Invalid status"}, status=400)


@login_required
@role_required("owner", "manager")
@require_POST
def table_assign_waiter(request, table_id):
    table = get_object_or_404(Table, id=table_id)
    waiter_id = request.POST.get("waiter_id")
    if waiter_id:
        waiter = get_object_or_404(User, id=waiter_id, role="waiter")
        table.assigned_waiter = waiter
    else:
        table.assigned_waiter = None
    table.save(update_fields=["assigned_waiter"])
    log_activity(request.user, "update", f"Assigned waiter to table {table.number}", "Table", table.id, request)
    messages.success(request, "Waiter assignment updated.")
    return redirect("table_list")
