"""Public (guest) ordering and order tracking views."""
import json
from decimal import Decimal

from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from .models import Order, OrderItem, Table
from apps.menu.models import MenuItem, MenuItemVariant
from apps.customers.models import Customer
from apps.accounts.models import RestaurantSettings


@require_http_methods(["POST"])
def public_create_order(request):
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid request body."}, status=400)

    items_data = data.get("items") or []
    if not items_data:
        return JsonResponse({"success": False, "error": "Your cart is empty."}, status=400)

    name = (data.get("name") or "").strip() or "Guest"
    phone = (data.get("phone") or "").strip()
    email = (data.get("email") or "").strip()
    order_type = data.get("order_type") or "takeaway"
    notes = (data.get("notes") or "").strip()

    if order_type not in dict(Order.OrderType.choices):
        order_type = Order.OrderType.TAKEAWAY

    settings_obj = RestaurantSettings.get_solo()
    tax_rate = settings_obj.tax_rate or 0

    customer = None
    if phone:
        customer, _ = Customer.objects.get_or_create(
            phone=phone,
            defaults={"name": name, "email": email},
        )
        if name != "Guest" and customer.name != name:
            customer.name = name
        if email and not customer.email:
            customer.email = email
        customer.save(update_fields=["name", "email"])

    try:
        with transaction.atomic():
            table = None
            table_id = data.get("table_id")
            if table_id and order_type == "dine_in":
                try:
                    table = Table.objects.get(id=table_id)
                except (Table.DoesNotExist, ValueError):
                    return JsonResponse({"success": False, "error": "Invalid table."}, status=400)
                if table.status not in (Table.Status.AVAILABLE, Table.Status.RESERVED):
                    return JsonResponse({"success": False, "error": f"Table {table.number} is not available."}, status=400)
                table.status = Table.Status.OCCUPIED
                table.save(update_fields=["status"])

            order = Order.objects.create(
                table=table,
                customer=customer,
                order_type=order_type,
                status=Order.Status.CONFIRMED,
                created_by=None,
                notes=notes,
            )

            subtotal = Decimal("0.00")
            for item_data in items_data:
                try:
                    menu_item = MenuItem.objects.get(id=int(item_data["menu_item_id"]), is_available=True)
                except (MenuItem.DoesNotExist, KeyError, ValueError, TypeError):
                    raise ValueError("One of the selected items is no longer available.")
                try:
                    qty = int(item_data.get("quantity", 1))
                except (TypeError, ValueError):
                    return JsonResponse({"success": False, "error": "Invalid quantity."}, status=400)
                if qty < 1 or qty > 99:
                    return JsonResponse({"success": False, "error": "Quantity must be between 1 and 99."}, status=400)

                if menu_item.available_quantity is not None:
                    if menu_item.available_quantity < qty:
                        raise ValueError(f"Only {menu_item.available_quantity} left of {menu_item.name}.")
                    menu_item.available_quantity -= qty
                    menu_item.save(update_fields=["available_quantity", "updated_at"])
                    if menu_item.available_quantity == 0:
                        menu_item.is_available = False
                        menu_item.save(update_fields=["is_available", "updated_at"])

                # A guest may have picked a variant (e.g. "Large") for this item.
                variant = None
                variant_id = item_data.get("variant_id")
                if variant_id:
                    try:
                        variant = MenuItemVariant.objects.get(
                            id=int(variant_id), menu_item=menu_item, is_available=True
                        )
                    except (MenuItemVariant.DoesNotExist, ValueError, TypeError):
                        raise ValueError("That option is no longer available.")
                unit_price = menu_item.price + (variant.price_adjustment if variant else Decimal("0"))
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    variant=variant,
                    quantity=qty,
                    unit_price=unit_price,
                    notes=(item_data.get("notes") or "").strip(),
                    status=OrderItem.ItemStatus.PENDING,
                )
                subtotal += unit_price * qty

            tax = (subtotal * Decimal(str(tax_rate)) / Decimal("100")).quantize(Decimal("0.01"))
            total = subtotal + tax
            order.subtotal = subtotal
            order.tax = tax
            order.total = total
            order.save(update_fields=["subtotal", "tax", "total", "updated_at"])

            if customer:
                try:
                    customer.add_points(total)
                except Exception:
                    pass

            tracking_url = reverse("public_order_track", args=[str(order.tracking_token)])
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "tracking_token": str(order.tracking_token),
                "tracking_url": tracking_url,
                "total": str(total),
                "message": f"Order {order.order_number} placed successfully!",
            })
    except ValueError as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def public_order_track(request, token):
    order = get_object_or_404(Order, tracking_token=token)
    return render(request, "orders/track.html", {"order": order, "token": token})


def public_order_status_api(request, token):
    order = get_object_or_404(
        Order.objects.select_related("table", "customer").prefetch_related(
            "items__menu_item", "items__variant"
        ),
        tracking_token=token,
    )
    now = timezone.now()
    items = []
    for item in order.items.all():
        display_name = item.menu_item.name
        if item.variant_id and item.variant:
            display_name = f"{display_name} — {item.variant.name}"
        items.append({
            "id": item.id,
            "name": display_name,
            "quantity": item.quantity,
            "status": item.status,
            "status_display": item.get_status_display(),
            "unit_price": str(item.unit_price),
            "line_total": str(item.line_total),
        })
    return JsonResponse({
        "order_number": order.order_number,
        "status": order.status,
        "status_display": order.get_status_display(),
        "order_type": order.order_type,
        "order_type_display": order.get_order_type_display(),
        "subtotal": str(order.subtotal),
        "tax": str(order.tax),
        "total": str(order.total),
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "completed_at": order.completed_at.isoformat() if order.completed_at else None,
        "items": items,
        "estimated_minutes": order.items.first().menu_item.preparation_time if order.items.exists() else None,
        "server_time": now.isoformat(),
    })


def public_track_lookup(request):
    """Let customers look up an order by number (and optional phone)."""
    error = None
    if request.method == "POST":
        order_number = (request.POST.get("order_number") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        qs = Order.objects.all()
        if order_number:
            qs = qs.filter(order_number__iexact=order_number)
        if phone:
            qs = qs.filter(customer__phone=phone)
        order = qs.first()
        if order is None and order_number:
            # Try a contains match as a fallback for mistyped characters
            order = Order.objects.filter(order_number__icontains=order_number).first()
        if order:
            return redirect("public_order_track", token=order.tracking_token)
        error = "We couldn't find a matching order. Please double-check your order number."
    return render(request, "orders/track_lookup.html", {"error": error})