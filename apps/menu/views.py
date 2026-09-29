from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Category, MenuItem
from apps.accounts.views import log_activity, role_required
import json


@login_required
def menu_list(request):
    categories = Category.objects.filter(is_active=True).prefetch_related("items")
    all_categories = Category.objects.all()
    return render(request, "menu/list.html", {
        "categories": categories,
        "all_categories": all_categories,
    })


@login_required
@role_required("owner", "manager")
@require_POST
def menu_item_toggle(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.is_available = not item.is_available
    item.save(update_fields=["is_available", "updated_at"])
    log_activity(
        request.user, "status_change",
        f"Menu item '{item.name}' set to {'available' if item.is_available else 'unavailable'}",
        "MenuItem", item.id, request,
    )
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.content_type == "application/json":
        return JsonResponse({"success": True, "is_available": item.is_available})
    messages.success(request, f"{item.name} is now {'available' if item.is_available else 'unavailable'}.")
    return redirect("menu_list")


@login_required
@role_required("owner", "manager")
@require_POST
def menu_item_create(request):
    name = request.POST.get("name", "").strip()
    category_id = request.POST.get("category_id")
    price = request.POST.get("price", "0")
    description = request.POST.get("description", "")
    if not name or not category_id:
        messages.error(request, "Name and category are required.")
        return redirect("menu_list")
    category = get_object_or_404(Category, id=category_id)
    try:
        price = Decimal(price)
    except Exception:
        price = Decimal("0")
    item = MenuItem.objects.create(
        name=name, category=category, price=price, description=description, is_available=True
    )
    log_activity(request.user, "create", f"Created menu item '{name}'", "MenuItem", item.id, request)
    messages.success(request, f"Menu item '{name}' created.")
    return redirect("menu_list")


@login_required
@role_required("owner", "manager")
@require_POST
def category_create(request):
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Category name is required.")
        return redirect("menu_list")
    cat, created = Category.objects.get_or_create(name=name)
    if created:
        log_activity(request.user, "create", f"Created category '{name}'", "Category", cat.id, request)
        messages.success(request, f"Category '{name}' created.")
    else:
        messages.info(request, f"Category '{name}' already exists.")
    return redirect("menu_list")
