from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Avg, ExpressionWrapper, DurationField
from django.db.models.functions import Extract
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import Order, OrderItem, Table
from apps.inventory.models import Ingredient
from apps.menu.models import MenuItem
import json


@login_required
def dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=6)

    today_orders = Order.objects.filter(created_at__date=today, status__in=["completed", "served"])
    today_revenue = today_orders.aggregate(total=Sum("total"))["total"] or 0
    today_count = today_orders.count()

    week_orders = Order.objects.filter(created_at__date__gte=week_ago, status__in=["completed", "served"])
    week_revenue = week_orders.aggregate(total=Sum("total"))["total"] or 0

    low_stock = list(Ingredient.objects.filter(current_stock__lte=F("minimum_stock"))[:5])

    top_items = list(
        OrderItem.objects.filter(order__created_at__date__gte=week_ago, order__status__in=["completed", "served"])
        .values("menu_item__name")
        .annotate(qty=Sum("quantity"))
        .order_by("-qty")[:5]
    )

    recent_orders = Order.objects.select_related("table", "created_by").order_by("-created_at")[:8]

    occupied_tables = Table.objects.filter(status="occupied").count()
    total_tables = Table.objects.count()

    # Sales chart
    sales_labels, sales_data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_total = (
            Order.objects.filter(created_at__date=day, status__in=["completed", "served"])
            .aggregate(total=Sum("total"))["total"] or 0
        )
        sales_labels.append(day.strftime("%a %d"))
        sales_data.append(float(day_total))

    top_labels = [item["menu_item__name"] for item in top_items]
    top_data = [item["qty"] for item in top_items]

    # ===== Prep & Service time analytics (last 7 days) =====
    timed_items = OrderItem.objects.filter(
        order__created_at__date__gte=week_ago,
        preparing_at__isnull=False,
        ready_at__isnull=False,
    )
    prep_times = []
    for item in timed_items[:200]:
        if item.prep_time_minutes is not None:
            prep_times.append(item.prep_time_minutes)
    avg_prep = round(sum(prep_times) / len(prep_times), 1) if prep_times else None

    service_times = []
    finished = Order.objects.filter(
        created_at__date__gte=week_ago,
        completed_at__isnull=False,
        status__in=["completed", "served"],
    )
    for o in finished[:200]:
        mins = (o.completed_at - o.created_at).total_seconds() / 60
        service_times.append(mins)
    avg_service = round(sum(service_times) / len(service_times), 1) if service_times else None

    # Order volume by hour (today) for a simple insight
    from django.db.models.functions import TruncHour
    hourly = (
        Order.objects.filter(created_at__date=today)
        .annotate(hour=TruncHour("created_at"))
        .values("hour")
        .annotate(count=Count("id"))
        .order_by("hour")
    )
    peak_hour = None
    if hourly:
        peak = max(hourly, key=lambda x: x["count"])
        if peak["hour"]:
            peak_hour = peak["hour"].strftime("%H:00")

    context = {
        "today_revenue": today_revenue,
        "today_count": today_count,
        "week_revenue": week_revenue,
        "low_stock": low_stock,
        "top_items": top_items,
        "recent_orders": recent_orders,
        "occupied_tables": occupied_tables,
        "total_tables": total_tables,
        "sales_labels": json.dumps(sales_labels),
        "sales_data": json.dumps(sales_data),
        "top_labels": json.dumps(top_labels),
        "top_data": json.dumps(top_data),
        "avg_prep_minutes": avg_prep,
        "avg_service_minutes": avg_service,
        "peak_hour": peak_hour,
        "prep_sample_count": len(prep_times),
        "service_sample_count": len(service_times),
    }
    return render(request, "dashboard/index.html", context)
