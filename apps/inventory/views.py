from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Ingredient, StockAdjustment
from apps.accounts.views import log_activity, role_required


@login_required
def inventory_list(request):
    ingredients = Ingredient.objects.all().order_by("name")
    low_stock = [i for i in ingredients if i.is_low_stock]
    recent_adjustments = StockAdjustment.objects.select_related("ingredient", "adjusted_by")[:15]
    return render(request, "inventory/list.html", {
        "ingredients": ingredients,
        "low_stock_count": len(low_stock),
        "recent_adjustments": recent_adjustments,
        "reason_choices": StockAdjustment.Reason.choices,
    })


@login_required
@role_required("owner", "manager", "cashier")
@require_POST
def stock_adjust(request):
    ingredient_id = request.POST.get("ingredient_id")
    quantity = request.POST.get("quantity")
    reason = request.POST.get("reason", "correction")
    notes = request.POST.get("notes", "")

    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    try:
        qty = Decimal(quantity)
    except Exception:
        messages.error(request, "Invalid quantity.")
        return redirect("inventory_list")

    ingredient.current_stock += qty
    if ingredient.current_stock < 0:
        ingredient.current_stock = 0
    ingredient.save(update_fields=["current_stock", "updated_at"])

    adj = StockAdjustment.objects.create(
        ingredient=ingredient,
        quantity_change=qty,
        reason=reason,
        notes=notes,
        adjusted_by=request.user,
    )
    log_activity(
        request.user, "stock_adjust",
        f"{ingredient.name}: {'+' if qty >= 0 else ''}{qty} ({reason})",
        "Ingredient", ingredient.id, request,
    )
    messages.success(request, f"Stock updated for {ingredient.name}.")
    return redirect("inventory_list")
