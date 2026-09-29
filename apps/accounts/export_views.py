import csv
import json
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from apps.accounts.views import role_required, log_activity
from apps.orders.models import Order, OrderItem, Table
from apps.menu.models import MenuItem, Category
from apps.inventory.models import Ingredient, StockAdjustment
from apps.accounts.models import User, ActivityLog
from apps.customers.models import Customer


@login_required
@role_required("owner", "manager")
def export_page(request):
    return render(request, "accounts/export.html")


@login_required
@role_required("owner", "manager")
def export_orders_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="orders_{datetime.now():%Y%m%d_%H%M}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Order Number", "Type", "Status", "Table", "Subtotal", "Tax", "Discount", "Total",
        "Created By", "Created At", "Completed At", "Notes",
    ])
    for o in Order.objects.select_related("table", "created_by").order_by("-created_at")[:2000]:
        writer.writerow([
            o.order_number, o.order_type, o.status,
            o.table.number if o.table else "",
            o.subtotal, o.tax, o.discount, o.total,
            o.created_by.username if o.created_by else "",
            o.created_at.strftime("%Y-%m-%d %H:%M"),
            o.completed_at.strftime("%Y-%m-%d %H:%M") if o.completed_at else "",
            (o.notes or "").replace("\n", " "),
        ])
    log_activity(request.user, "other", "Exported orders CSV", request=request)
    return response


@login_required
@role_required("owner", "manager")
def export_inventory_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="inventory_{datetime.now():%Y%m%d_%H%M}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Unit", "Current Stock", "Minimum Stock", "Cost Per Unit", "Supplier", "Low Stock"])
    for i in Ingredient.objects.all().order_by("name"):
        writer.writerow([i.name, i.unit, i.current_stock, i.minimum_stock, i.cost_per_unit, i.supplier, i.is_low_stock])
    log_activity(request.user, "other", "Exported inventory CSV", request=request)
    return response


@login_required
@role_required("owner", "manager")
def export_menu_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="menu_{datetime.now():%Y%m%d_%H%M}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Category", "Name", "Description", "Price", "Available", "Featured", "Prep Time (min)"])
    for item in MenuItem.objects.select_related("category").order_by("category__name", "name"):
        writer.writerow([
            item.category.name, item.name, item.description, item.price,
            item.is_available, item.is_featured, item.preparation_time,
        ])
    log_activity(request.user, "other", "Exported menu CSV", request=request)
    return response


@login_required
@role_required("owner", "manager")
def export_full_backup_json(request):
    """JSON dump of core data for backup."""
    data = {
        "exported_at": datetime.now().isoformat(),
        "exported_by": request.user.username,
        "categories": list(Category.objects.values("id", "name", "description", "is_active", "sort_order")),
        "menu_items": list(MenuItem.objects.values(
            "id", "category_id", "name", "description", "price", "is_available", "is_featured", "preparation_time"
        )),
        "ingredients": list(Ingredient.objects.values(
            "id", "name", "unit", "current_stock", "minimum_stock", "cost_per_unit", "supplier"
        )),
        "tables": list(Table.objects.values("id", "number", "capacity", "status", "location")),
        "orders": [],
    }
    for o in Order.objects.select_related("table", "created_by").prefetch_related("items")[:1000]:
        data["orders"].append({
            "order_number": o.order_number,
            "status": o.status,
            "order_type": o.order_type,
            "table": o.table.number if o.table else None,
            "subtotal": str(o.subtotal),
            "tax": str(o.tax),
            "discount": str(o.discount),
            "total": str(o.total),
            "notes": o.notes,
            "created_at": o.created_at.isoformat(),
            "completed_at": o.completed_at.isoformat() if o.completed_at else None,
            "items": [
                {
                    "name": i.menu_item.name,
                    "quantity": i.quantity,
                    "unit_price": str(i.unit_price),
                    "status": i.status,
                }
                for i in o.items.all()
            ],
        })

    response = HttpResponse(json.dumps(data, indent=2, default=str), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="restaurant_backup_{datetime.now():%Y%m%d_%H%M}.json"'
    log_activity(request.user, "other", "Exported full JSON backup", request=request)
    return response
