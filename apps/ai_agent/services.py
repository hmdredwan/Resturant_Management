from django.conf import settings
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
import os

# Try to import groq, fallback gracefully
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


SYSTEM_PROMPT = """You are an intelligent Restaurant AI Assistant for a modern restaurant management system called RestaurantAI.
You help managers and staff with insights about sales, inventory, menu performance, and operational suggestions.
Be professional, concise, data-driven, and helpful. Use clear formatting with bullet points when listing items.
When you don't have exact data, say so and give general best-practice advice.
"""


def get_restaurant_context():
    """Build live context from the database for the AI."""
    try:
        from apps.orders.models import Order, OrderItem
        from apps.inventory.models import Ingredient
        from apps.menu.models import MenuItem

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # Today's performance
        today_orders = Order.objects.filter(created_at__date=today, status="completed")
        today_revenue = today_orders.aggregate(total=Sum("total"))["total"] or 0
        today_count = today_orders.count()

        # Low stock
        low_stock = Ingredient.objects.filter(current_stock__lte=F("minimum_stock"))
        low_stock_list = [f"{i.name} ({i.current_stock} {i.unit})" for i in low_stock[:8]]

        # Top selling items (last 7 days)
        top_items = (
            OrderItem.objects.filter(
                order__created_at__date__gte=week_ago,
                order__status="completed"
            )
            .values("menu_item__name")
            .annotate(qty=Sum("quantity"))
            .order_by("-qty")[:5]
        )
        top_items_str = ", ".join([f"{i['menu_item__name']} ({i['qty']})" for i in top_items]) or "No data yet"

        # Active orders
        active_orders = Order.objects.filter(status__in=["pending", "confirmed", "preparing", "ready"]).count()

        context = f"""
=== LIVE RESTAURANT DATA ===
Date: {today}
Today's Revenue: ${today_revenue}
Today's Completed Orders: {today_count}
Active Orders (in progress): {active_orders}
Low Stock Items: {', '.join(low_stock_list) if low_stock_list else 'None'}
Top Selling Items (7 days): {top_items_str}
=============================
"""
        return context
    except Exception as e:
        return f"(Could not load live data: {e})"


def ask_ai_agent(user_message: str, conversation_history: list = None) -> str:
    """
    Send a message to the AI agent with live restaurant context.
    Falls back to a helpful mock response if no API key is configured.
    """
    context = get_restaurant_context()
    full_system = SYSTEM_PROMPT + "\n\n" + context

    # If no API key, return a smart mock response
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    if not api_key or not GROQ_AVAILABLE:
        return _mock_response(user_message, context)

    try:
        client = Groq(api_key=api_key)
        messages = [{"role": "system", "content": full_system}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI service temporarily unavailable. ({str(e)[:100]})\n\nBased on current data:\n{context}"


def _mock_response(user_message: str, context: str) -> str:
    """Helpful fallback when no API key is set."""
    msg = user_message.lower()
    
    if any(w in msg for w in ["sales", "revenue", "today", "earning"]):
        return f"📊 **Sales Overview**\n\nHere's what I can see from the live data:\n\n{context}\n\n💡 Tip: Connect a Groq API key in your `.env` file for more advanced analysis and natural language reports."
    
    if any(w in msg for w in ["stock", "inventory", "low", "ingredient"]):
        return f"📦 **Inventory Status**\n\n{context}\n\nI recommend checking the Inventory page for full details and restocking low items soon."
    
    if any(w in msg for w in ["menu", "popular", "recommend", "suggest"]):
        return f"🍽️ **Menu Insights**\n\n{context}\n\nBased on top sellers, consider promoting high-performing items or creating combos. Would you like me to suggest a promotion?"
    
    if any(w in msg for w in ["help", "what can you", "hello", "hi"]):
        return """👋 **Hello! I'm your Restaurant AI Assistant.**

I can help you with:
- 📈 Sales & revenue summaries
- 📦 Inventory & low-stock alerts
- 🍽️ Menu performance & suggestions
- 📋 Daily/weekly reports
- 💡 Operational recommendations

Just ask me anything about the restaurant!

*(Currently running in demo mode. Add a `GROQ_API_KEY` to `.env` for full AI power.)*"""
    
    return f"I received your question: \"{user_message}\"\n\nHere's the current restaurant snapshot:\n{context}\n\nFor full intelligent responses, please add your Groq API key to the `.env` file."
