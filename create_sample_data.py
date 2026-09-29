"""
Run this after migrations:
python manage.py shell < create_sample_data.py
or
python manage.py shell
>>> exec(open('create_sample_data.py').read())
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.menu.models import Category, MenuItem
from apps.inventory.models import Ingredient
from apps.orders.models import Table
from decimal import Decimal

User = get_user_model()

# Create superuser if not exists
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@restaurant.ai',
        password='admin123',
        role='owner',
        first_name='Admin',
        last_name='User'
    )
    print("✓ Superuser created: admin / admin123")

# Create sample categories & items
categories_data = [
    ("Starters", "Appetizers and small plates"),
    ("Main Course", "Hearty main dishes"),
    ("Desserts", "Sweet endings"),
    ("Beverages", "Drinks and refreshments"),
]

for name, desc in categories_data:
    cat, created = Category.objects.get_or_create(name=name, defaults={"description": desc})
    if created:
        print(f"✓ Category: {name}")

# Sample menu items
items = [
    ("Starters", "Garlic Bread", "Toasted bread with garlic butter", Decimal("5.99")),
    ("Starters", "Caesar Salad", "Fresh romaine, parmesan, croutons", Decimal("8.99")),
    ("Starters", "Soup of the Day", "Chef's daily special soup", Decimal("6.50")),
    ("Main Course", "Grilled Chicken", "Herb-marinated chicken breast with veggies", Decimal("16.99")),
    ("Main Course", "Beef Burger", "Angus beef, cheese, fries", Decimal("14.99")),
    ("Main Course", "Pasta Carbonara", "Creamy pasta with bacon", Decimal("13.99")),
    ("Main Course", "Margherita Pizza", "Classic tomato, mozzarella, basil", Decimal("12.99")),
    ("Desserts", "Chocolate Cake", "Rich chocolate layer cake", Decimal("7.99")),
    ("Desserts", "Ice Cream", "Vanilla / Chocolate / Strawberry", Decimal("4.99")),
    ("Beverages", "Fresh Lemonade", "House-made lemonade", Decimal("3.99")),
    ("Beverages", "Coffee", "Freshly brewed", Decimal("2.99")),
    ("Beverages", "Soft Drink", "Coke / Sprite / Fanta", Decimal("2.50")),
]

for cat_name, name, desc, price in items:
    cat = Category.objects.get(name=cat_name)
    item, created = MenuItem.objects.get_or_create(
        name=name,
        category=cat,
        defaults={"description": desc, "price": price, "is_available": True}
    )
    if created:
        print(f"✓ Menu item: {name}")

# Sample ingredients
ingredients = [
    ("Chicken Breast", "kg", 15, 5, Decimal("8.50")),
    ("Beef Patty", "pcs", 40, 10, Decimal("2.20")),
    ("Pasta", "kg", 8, 3, Decimal("1.80")),
    ("Tomato Sauce", "liter", 12, 4, Decimal("3.00")),
    ("Mozzarella", "kg", 6, 2, Decimal("9.00")),
    ("Lettuce", "kg", 3, 2, Decimal("2.50")),
    ("Garlic", "kg", 1.5, 1, Decimal("4.00")),
    ("Coffee Beans", "kg", 4, 1.5, Decimal("12.00")),
]

for name, unit, stock, minimum, cost in ingredients:
    ing, created = Ingredient.objects.get_or_create(
        name=name,
        defaults={
            "unit": unit,
            "current_stock": stock,
            "minimum_stock": minimum,
            "cost_per_unit": cost,
        }
    )
    if created:
        print(f"✓ Ingredient: {name}")

# Sample tables
for i in range(1, 11):
    Table.objects.get_or_create(number=str(i), defaults={"capacity": 4 if i < 8 else 6})
print("✓ 10 tables created")

print("\n✅ Sample data loaded successfully!")
print("Login with: admin / admin123")
