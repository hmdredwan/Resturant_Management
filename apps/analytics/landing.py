from django.shortcuts import render
from apps.menu.models import Category, MenuItem
from apps.accounts.models import RestaurantSettings


def home(request):
    """Public marketing homepage with live menu from admin-managed items."""
    restaurant = RestaurantSettings.get_solo()
    categories = (
        Category.objects.filter(is_active=True)
        .prefetch_related("items")
        .order_by("sort_order", "name")
    )
    available_items = MenuItem.objects.filter(is_available=True).select_related("category").order_by(
        "-is_featured", "category__sort_order", "name"
    )
    featured_items = available_items.filter(is_featured=True)[:6]

    # Currency symbol helper fallback
    currency = restaurant.currency or "USD"
    currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "BDT": "৳", "INR": "₹"}
    symbol = currency_symbols.get(currency, "$")

    context = {
        "restaurant": restaurant,
        "categories": categories,
        "available_items": available_items,
        "featured_items": featured_items,
        "currency": currency,
        "currency_symbol": symbol,
    }
    return render(request, "landing/home.html", context)