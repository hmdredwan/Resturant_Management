from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.urls import reverse
from decimal import Decimal
from .models import Category, MenuItem, MenuItemVariant
from apps.accounts.views import log_activity, role_required
from apps.accounts.models import RestaurantSettings
import json


@login_required
def menu_list(request):
    categories = (
        Category.objects.filter(is_active=True)
        .prefetch_related("items__variants")
        .order_by("sort_order", "name")
    )
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
    description = request.POST.get("description", "").strip()
    is_available = request.POST.get("is_available") in ("on", "true", "1")
    is_featured = request.POST.get("is_featured") in ("on", "true", "1")
    prep_time = request.POST.get("preparation_time", "15") or "15"
    calories = request.POST.get("calories", "").strip()
    portion_size = request.POST.get("portion_size", "").strip()
    available_quantity = request.POST.get("available_quantity", "").strip()
    is_vegetarian = request.POST.get("is_vegetarian") in ("on", "true", "1")
    is_vegan = request.POST.get("is_vegan") in ("on", "true", "1")
    is_gluten_free = request.POST.get("is_gluten_free") in ("on", "true", "1")
    allergens = request.POST.get("allergens", "").strip()

    if not name or not category_id:
        messages.error(request, "Name and category are required.")
        return redirect("menu_list")
    category = get_object_or_404(Category, id=category_id)
    try:
        price = Decimal(price)
    except Exception:
        price = Decimal("0")
    try:
        prep_time = int(prep_time)
    except (TypeError, ValueError):
        prep_time = 15
    calories_val = None
    if calories:
        try:
            calories_val = int(calories)
        except (TypeError, ValueError):
            calories_val = None
    quantity_val = None
    if available_quantity:
        try:
            quantity_val = int(available_quantity)
        except (TypeError, ValueError):
            quantity_val = None

    item = MenuItem.objects.create(
        name=name,
        category=category,
        price=price,
        description=description,
        image=request.FILES.get("image"),
        is_available=True,
        is_featured=is_featured,
        preparation_time=prep_time,
        calories=calories_val,
        portion_size=portion_size,
        available_quantity=quantity_val,
        is_vegetarian=is_vegetarian,
        is_vegan=is_vegan,
        is_gluten_free=is_gluten_free,
        allergens=allergens,
    )
    log_activity(request.user, "create", f"Created menu item '{name}'", "MenuItem", item.id, request)
    messages.success(request, f"Menu item '{name}' created.")
    return redirect("menu_list")

@login_required
@role_required("owner", "manager")
@require_POST
def menu_item_delete(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    name = item.name
    item.delete()
    log_activity(request.user, "delete", f"Deleted menu item '{name}'", "MenuItem", item_id, request)
    messages.success(request, f"Menu item '{name}' deleted.")
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


def _parse_adjustment(value):
    try:
        return Decimal(value or "0")
    except Exception:
        return Decimal("0")


@login_required
@role_required("owner", "manager")
@require_POST
def variant_create(request):
    """Create a variant (e.g. 'Large', 'Extra Cheese') for a menu item."""
    menu_item = get_object_or_404(MenuItem, id=request.POST.get("menu_item_id", ""))
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Variant name is required.")
        return redirect("menu_list")
    variant = MenuItemVariant.objects.create(
        menu_item=menu_item,
        name=name,
        price_adjustment=_parse_adjustment(request.POST.get("price_adjustment")),
        is_available=request.POST.get("is_available") in ("on", "true", "1"),
    )
    log_activity(
        request.user, "create",
        f"Created variant '{name}' for menu item '{menu_item.name}'",
        "MenuItemVariant", variant.id, request,
    )
    messages.success(request, f"Variant '{name}' created.")
    return redirect("menu_list")


@login_required
@role_required("owner", "manager")
@require_POST
def variant_update(request, variant_id):
    """Edit a variant: rename it, change its price adjustment or availability."""
    variant = get_object_or_404(MenuItemVariant, id=variant_id)
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Variant name is required.")
        return redirect("menu_list")
    variant.name = name
    variant.price_adjustment = _parse_adjustment(request.POST.get("price_adjustment"))
    variant.is_available = request.POST.get("is_available") in ("on", "true", "1")
    variant.save(update_fields=["name", "price_adjustment", "is_available"])
    log_activity(
        request.user, "update",
        f"Updated variant '{name}' for menu item '{variant.menu_item.name}'",
        "MenuItemVariant", variant.id, request,
    )
    messages.success(request, f"Variant '{name}' updated.")
    return redirect("menu_list")


@login_required
@role_required("owner", "manager")
@require_POST
def variant_delete(request, variant_id):
    """Delete a variant (e.g. 'Large') from a menu item."""
    variant = get_object_or_404(MenuItemVariant, id=variant_id)
    item_name = variant.menu_item.name
    variant_name = variant.name
    variant.delete()
    log_activity(
        request.user, "delete",
        f"Deleted variant '{variant_name}' from menu item '{item_name}'",
        "MenuItemVariant", variant_id, request,
    )
    messages.success(request, f"Variant '{variant_name}' deleted.")
    return redirect("menu_list")
