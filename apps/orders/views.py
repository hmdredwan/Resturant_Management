from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json
from .models import Order, OrderItem, Table
from apps.menu.models import MenuItem, Category


@login_required
def pos_view(request):
    tables = Table.objects.all()
    categories = Category.objects.filter(is_active=True).prefetch_related("items")
    menu_items = MenuItem.objects.filter(is_available=True).select_related("category")
    
    context = {
        "tables": tables,
        "categories": categories,
        "menu_items": menu_items,
    }
    return render(request, "pos/index.html", context)


@login_required
def order_list(request):
    from django.db.models import Q

    qs = Order.objects.select_related("table", "created_by", "customer").prefetch_related("items").order_by("-created_at")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    order_type = request.GET.get("type", "").strip()
    date_from = request.GET.get("from", "").strip()
    date_to = request.GET.get("to", "").strip()

    if q:
        qs = qs.filter(
            Q(order_number__icontains=q)
            | Q(table__number__icontains=q)
            | Q(customer__name__icontains=q)
            | Q(customer__phone__icontains=q)
            | Q(notes__icontains=q)
            | Q(created_by__username__icontains=q)
            | Q(created_by__first_name__icontains=q)
            | Q(created_by__last_name__icontains=q)
        )

    if status:
        qs = qs.filter(status=status)

    if order_type:
        qs = qs.filter(order_type=order_type)

    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)

    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    orders = qs[:100]

    context = {
        "orders": orders,
        "q": q,
        "status": status,
        "order_type": order_type,
        "date_from": date_from,
        "date_to": date_to,
        "status_choices": Order.Status.choices,
        "type_choices": Order.OrderType.choices,
        "result_count": qs.count(),
    }
    return render(request, "orders/list.html", context)


@login_required
def kitchen_display(request):
    active_items = (
        OrderItem.objects.filter(status__in=["pending", "preparing", "ready"])
        .select_related("order", "menu_item", "order__table")
        .order_by("created_at")
    )
    return render(request, "kitchen/display.html", {"items": active_items})


@login_required
def kitchen_feed_api(request):
    """JSON feed for real-time kitchen display polling."""
    items = (
        OrderItem.objects.filter(status__in=["pending", "preparing", "ready"])
        .select_related("order", "menu_item", "order__table")
        .order_by("created_at")
    )
    now = timezone.now()
    data = []
    for item in items:
        age_seconds = int((now - item.created_at).total_seconds())
        # Priority: older pending/preparing items rank higher
        priority = age_seconds
        if item.status == "pending":
            priority += 10000
        elif item.status == "preparing":
            priority += 5000
        data.append({
            "id": item.id,
            "order_id": item.order_id,
            "order_number": item.order.order_number,
            "table": item.order.table.number if item.order.table else None,
            "item_name": item.menu_item.name,
            "quantity": item.quantity,
            "notes": item.notes or "",
            "status": item.status,
            "status_display": item.get_status_display(),
            "created_at": item.created_at.isoformat(),
            "age_seconds": age_seconds,
            "age_display": _format_age(age_seconds),
            "priority": priority,
            "is_urgent": age_seconds > 600,  # > 10 minutes
        })
    data.sort(key=lambda x: -x["priority"])
    return JsonResponse({
        "items": data,
        "count": len(data),
        "server_time": now.isoformat(),
    })


def _format_age(seconds):
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    return f"{minutes // 60}h {minutes % 60}m"


@login_required
@require_POST
def update_item_status(request, item_id):
    item = get_object_or_404(OrderItem, id=item_id)
    try:
        data = json.loads(request.body) if request.body else {}
        new_status = data.get("status") or request.POST.get("status")
    except json.JSONDecodeError:
        new_status = request.POST.get("status")

    valid_statuses = dict(OrderItem.ItemStatus.choices)
    if new_status not in valid_statuses:
        return JsonResponse({"success": False, "error": "Invalid status"}, status=400)

    now = timezone.now()
    item.status = new_status
    update_fields = ["status"]
    if new_status == "preparing" and not item.preparing_at:
        item.preparing_at = now
        update_fields.append("preparing_at")
    elif new_status == "ready" and not item.ready_at:
        item.ready_at = now
        if not item.preparing_at:
            item.preparing_at = now
            update_fields.append("preparing_at")
        update_fields.append("ready_at")
    elif new_status == "served" and not item.served_at:
        item.served_at = now
        update_fields.append("served_at")
    item.save(update_fields=update_fields)

    # Update parent order status intelligently
    order = item.order
    item_statuses = set(order.items.values_list("status", flat=True))

    if item_statuses <= {"served", "cancelled"}:
        order.status = Order.Status.SERVED
        if not order.completed_at:
            order.completed_at = now
            if order.table:
                order.table.status = Table.Status.AVAILABLE
                order.table.save()
        order.save(update_fields=["status", "completed_at"])
    elif "ready" in item_statuses and not ({"pending", "preparing"} & item_statuses):
        order.status = Order.Status.READY
        order.save(update_fields=["status"])
    elif "preparing" in item_statuses or "ready" in item_statuses:
        order.status = Order.Status.PREPARING
        order.save(update_fields=["status"])
    elif "pending" in item_statuses:
        order.status = Order.Status.CONFIRMED
        order.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "status": item.status,
        "order_status": order.status,
        "item_id": item.id,
    })


@login_required
@require_http_methods(["POST"])
def create_order(request):
    """Create a new order from POS cart."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    items_data = data.get("items", [])
    table_id = data.get("table_id")
    order_type = data.get("order_type", "dine_in")
    notes = data.get("notes", "")

    if not items_data:
        return JsonResponse({"success": False, "error": "Cart is empty"}, status=400)

    try:
        with transaction.atomic():
            table = None
            if table_id:
                table = get_object_or_404(Table, id=table_id)
                if table.status == Table.Status.OCCUPIED:
                    return JsonResponse({"success": False, "error": f"Table {table.number} is already occupied"}, status=400)
                table.status = Table.Status.OCCUPIED
                table.save()

            order = Order.objects.create(
                table=table,
                order_type=order_type,
                status=Order.Status.CONFIRMED,
                created_by=request.user,
                notes=notes,
            )

            subtotal = Decimal("0.00")
            for item_data in items_data:
                menu_item = get_object_or_404(MenuItem, id=item_data["menu_item_id"], is_available=True)
                qty = int(item_data.get("quantity", 1))
                unit_price = menu_item.price
                notes_item = item_data.get("notes", "")

                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=qty,
                    unit_price=unit_price,
                    notes=notes_item,
                    status=OrderItem.ItemStatus.PENDING,
                )
                subtotal += unit_price * qty

            tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
            total = subtotal + tax

            order.subtotal = subtotal
            order.tax = tax
            order.total = total
            order.save(update_fields=["subtotal", "tax", "total"])

            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "order_number": order.order_number,
                "total": str(total),
                "message": f"Order {order.order_number} placed successfully!",
            })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def order_detail_api(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("table", "created_by", "customer")
        .prefetch_related("items__menu_item"),
        id=order_id,
    )
    user = request.user
    is_manager = user.role in ["owner", "manager", "cashier"] or user.is_superuser
    is_early = order.status in [Order.Status.PENDING, Order.Status.CONFIRMED, Order.Status.PREPARING, Order.Status.READY]
    is_creator_early = order.created_by_id == user.id and order.status in [Order.Status.PENDING, Order.Status.CONFIRMED]

    can_cancel = is_early and (is_manager or is_creator_early) and order.status not in [Order.Status.SERVED, Order.Status.COMPLETED, Order.Status.CANCELLED]
    can_edit = order.status not in [Order.Status.SERVED, Order.Status.COMPLETED, Order.Status.CANCELLED] and (is_manager or is_creator_early)

    items = [
        {
            "id": i.id,
            "name": i.menu_item.name,
            "quantity": i.quantity,
            "unit_price": str(i.unit_price),
            "line_total": str(i.quantity * i.unit_price),
            "status": i.status,
            "status_display": i.get_status_display(),
            "notes": i.notes or "",
            "prep_time_minutes": i.prep_time_minutes,
            "service_time_minutes": i.service_time_minutes,
        }
        for i in order.items.all()
    ]
    return JsonResponse({
        "id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "status_display": order.get_status_display(),
        "order_type": order.order_type,
        "order_type_display": order.get_order_type_display(),
        "table": order.table.number if order.table else None,
        "customer": order.customer.name if order.customer else None,
        "created_by": order.created_by.get_full_name() or order.created_by.username if order.created_by else None,
        "subtotal": str(order.subtotal),
        "tax": str(order.tax),
        "discount": str(order.discount),
        "total": str(order.total),
        "notes": order.notes or "",
        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M"),
        "completed_at": order.completed_at.strftime("%Y-%m-%d %H:%M") if order.completed_at else None,
        "items": items,
        "can_cancel": can_cancel,
        "can_edit": can_edit,
        "is_manager": is_manager,
    })


@login_required
@require_http_methods(["POST"])
def cancel_order(request, order_id):
    """Cancel an order. Allowed for owner/manager/cashier, or creator if still pending/confirmed."""
    from apps.accounts.views import log_activity

    order = get_object_or_404(Order, id=order_id)
    user = request.user

    if order.status in [Order.Status.COMPLETED, Order.Status.CANCELLED, Order.Status.SERVED]:
        return JsonResponse({"success": False, "error": f"Cannot cancel an order that is already {order.status}."}, status=400)

    # Authorization
    can_cancel = (
        user.role in ["owner", "manager", "cashier"]
        or user.is_superuser
        or (order.created_by_id == user.id and order.status in [Order.Status.PENDING, Order.Status.CONFIRMED])
    )
    if not can_cancel:
        return JsonResponse({"success": False, "error": "You are not authorized to cancel this order."}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    reason = data.get("reason", "").strip()

    order.status = Order.Status.CANCELLED
    if reason:
        order.notes = (order.notes + "\n" if order.notes else "") + f"[CANCELLED] {reason}"
    order.completed_at = timezone.now()
    order.save(update_fields=["status", "notes", "completed_at"])

    # Cancel all non-served items
    order.items.exclude(status=OrderItem.ItemStatus.SERVED).update(status=OrderItem.ItemStatus.CANCELLED)

    # Free table
    if order.table:
        order.table.status = Table.Status.AVAILABLE
        order.table.save()

    log_activity(user, "status_change", f"Cancelled order {order.order_number}" + (f": {reason}" if reason else ""), "Order", order.id, request)

    return JsonResponse({"success": True, "message": f"Order {order.order_number} cancelled.", "status": order.status})


@login_required
@require_http_methods(["POST"])
def edit_order(request, order_id):
    """
    Edit order notes, discount, or item quantities.
    Owner/manager/cashier can edit; waiter can edit notes if they created it and status is early.
    """
    from apps.accounts.views import log_activity

    order = get_object_or_404(Order.objects.prefetch_related("items"), id=order_id)
    user = request.user

    if order.status in [Order.Status.COMPLETED, Order.Status.CANCELLED, Order.Status.SERVED]:
        return JsonResponse({"success": False, "error": "Cannot edit a finished or cancelled order."}, status=400)

    is_manager = user.role in ["owner", "manager", "cashier"] or user.is_superuser
    is_creator_early = order.created_by_id == user.id and order.status in [Order.Status.PENDING, Order.Status.CONFIRMED]

    if not (is_manager or is_creator_early):
        return JsonResponse({"success": False, "error": "You are not authorized to edit this order."}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    changes = []

    # Notes
    if "notes" in data:
        order.notes = data["notes"] or ""
        changes.append("notes")

    # Discount (managers only)
    if "discount" in data and is_manager:
        try:
            order.discount = Decimal(str(data["discount"]))
            changes.append("discount")
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid discount"}, status=400)

    # Item quantity updates (managers or early creator)
    items_data = data.get("items", [])
    if items_data and (is_manager or is_creator_early):
        for item_data in items_data:
            item_id = item_data.get("id")
            qty = item_data.get("quantity")
            if item_id is None or qty is None:
                continue
            try:
                item = order.items.get(id=item_id)
                if item.status in [OrderItem.ItemStatus.SERVED, OrderItem.ItemStatus.CANCELLED]:
                    continue
                qty = int(qty)
                if qty <= 0:
                    item.status = OrderItem.ItemStatus.CANCELLED
                    item.save(update_fields=["status"])
                    changes.append(f"cancelled item {item.menu_item.name}")
                else:
                    item.quantity = qty
                    item.save(update_fields=["quantity"])
                    changes.append(f"qty {item.menu_item.name}={qty}")
            except OrderItem.DoesNotExist:
                continue

    # Recalculate totals
    subtotal = sum(i.line_total for i in order.items.exclude(status=OrderItem.ItemStatus.CANCELLED))
    order.subtotal = subtotal
    order.tax = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))
    order.total = order.subtotal + order.tax - order.discount
    order.save()

    log_activity(user, "update", f"Edited order {order.order_number}: {', '.join(changes) or 'no changes'}", "Order", order.id, request)

    return JsonResponse({
        "success": True,
        "message": "Order updated.",
        "subtotal": str(order.subtotal),
        "tax": str(order.tax),
        "discount": str(order.discount),
        "total": str(order.total),
        "status": order.status,
    })
