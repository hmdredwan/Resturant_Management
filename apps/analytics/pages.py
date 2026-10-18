from django.shortcuts import render
from django.contrib import messages
from apps.accounts.models import RestaurantSettings
from apps.menu.models import Category, MenuItem
from decimal import Decimal


def _restaurant_context():
    restaurant = RestaurantSettings.get_solo()
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "BDT": "৳", "INR": "₹"}
    currency = restaurant.currency or "USD"
    return restaurant, currency, symbols.get(currency, "$")


def public_menu(request):
    restaurant, currency, symbol = _restaurant_context()
    categories = (
        Category.objects.filter(is_active=True)
        .prefetch_related("items__variants")
        .order_by("sort_order", "name")
    )
    available_items = (
        MenuItem.objects.filter(is_available=True)
        .select_related("category")
        .prefetch_related("variants")
        .order_by("-is_featured", "name")
    )
    return render(request, "pages/menu.html", {
        "restaurant": restaurant, "categories": categories,
        "available_items": available_items, "currency": currency,
        "currency_symbol": symbol,
    })


def catering(request):
    restaurant, currency, symbol = _restaurant_context()
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        event_type = (request.POST.get("event_type") or "").strip()
        event_date = (request.POST.get("event_date") or "").strip()
        guests = (request.POST.get("guests") or "").strip()
        message_text = (request.POST.get("message") or "").strip()
        if not name or not (email or phone):
            messages.error(request, "Please provide your name and a way to contact you.")
        else:
            messages.success(request, f"Thank you, {name}! Our catering team will be in touch shortly.")
    packages = [
        {"name": "Intimate Gathering", "guests": "10–30 guests", "price": "From $45/guest", "icon": "bi-house-heart", "items": ["3-course curated menu", "Professional service staff", "Tableware & linens", "Setup & cleanup"]},
        {"name": "Corporate Event", "guests": "30–100 guests", "price": "From $55/guest", "icon": "bi-building", "items": ["Custom buffet or plated", "Dietary accommodations", "On-site coordinator", "Beverage package"]},
        {"name": "Grand Celebration", "guests": "100+ guests", "price": "Custom quote", "icon": "bi-stars", "items": ["Bespoke multi-course menu", "Live cooking stations", "Premium décor", "Full event management"]},
    ]
    return render(request, "pages/catering.html", {
        "restaurant": restaurant, "packages": packages,
    })


def consultancy(request):
    restaurant, currency, symbol = _restaurant_context()
    services = [
        {"icon": "bi-clipboard-data", "title": "Menu Engineering", "text": "Data-driven menu design to maximize profitability and guest satisfaction."},
        {"icon": "bi-people", "title": "Staff Training", "text": "Front-of-house and kitchen programs tailored to your concept and standards."},
        {"icon": "bi-gear", "title": "Operations Audit", "text": "End-to-end review of workflows, inventory, and service to reduce waste."},
        {"icon": "bi-graph-up-arrow", "title": "Revenue Strategy", "text": "Pricing, upselling, and experiential revenue optimization."},
        {"icon": "bi-brush", "title": "Concept Development", "text": "From brand identity to launch: naming, positioning, and market fit."},
        {"icon": "bi-shield-check", "title": "Food Safety Compliance", "text": "HACCP systems, SOPs, and certification readiness."},
    ]
    process = [
        {"step": "01", "title": "Discovery", "text": "We learn your vision, market, and constraints."},
        {"step": "02", "title": "Strategy", "text": "A tailored roadmap with measurable goals."},
        {"step": "03", "title": "Implementation", "text": "Hands-on execution alongside your team."},
        {"step": "04", "title": "Review", "text": "Ongoing support and outcome tracking."},
    ]
    return render(request, "pages/consultancy.html", {
        "restaurant": restaurant, "services": services, "process": process,
    })


def our_story(request):
    restaurant, currency, symbol = _restaurant_context()
    timeline = [
        {"year": "2020", "title": "The First Service", "text": "A small dining room and a big idea: food made with honesty, served with warmth."},
        {"year": "2021", "title": "Recognition", "text": "Our signature tasting menu earned its first regional award."},
        {"year": "2023", "title": "Expansion", "text": "We grew the team, deepened our supplier partnerships, and launched catering."},
        {"year": "2025", "title": "Today", "text": "A destination for refined dining — and a partner to restaurants and venues worldwide."},
    ]
    values = [
        {"icon": "bi-leaf", "title": "Seasonal Ingredients", "text": "Sourced locally, prepared at peak freshness."},
        {"icon": "bi-fire", "title": "Crafted Technique", "text": "Classical methods, modern sensibility."},
        {"icon": "bi-heart", "title": "Genuine Hospitality", "text": "Every guest leaves feeling valued."},
    ]
    return render(request, "pages/our_story.html", {
        "restaurant": restaurant, "timeline": timeline, "values": values,
    })


def founder_message(request):
    restaurant, currency, symbol = _restaurant_context()
    return render(request, "pages/founder_message.html", {"restaurant": restaurant})