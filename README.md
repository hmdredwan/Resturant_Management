# RestaurantAI – Dynamic Restaurant Management System

A modern, AI-powered restaurant management system built with **Django + Tailwind CSS + Bootstrap**.

## Features

- 📊 Real-time Dashboard with sales & inventory insights
- 🛒 Point of Sale (POS) with table management
- 👨‍🍳 Kitchen Display System
- 📋 Dynamic Menu Management
- 📦 Inventory & low-stock alerts
- 🤖 AI Assistant (Groq / OpenAI) for natural language insights
- 🌙 Dark / Light mode
- 📱 Fully responsive modern SaaS UI

## Tech Stack

- **Backend**: Django 5/6 + Django REST Framework
- **Frontend**: Tailwind CSS + Bootstrap 5 + custom animations
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **AI**: Groq (llama-3.3-70b) or OpenAI

## Quick Start

```bash
# 1. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Load sample data (optional but recommended)
python manage.py shell < create_sample_data.py

# 5. Create superuser (if you skipped sample data)
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

Open http://127.0.0.1:8000

**Demo login** (after sample data):  
Username: `admin`  
Password: `admin123`

## AI Assistant Setup

1. Get a free API key from [console.groq.com](https://console.groq.com)
2. Add it to `.env`:

```env
GROQ_API_KEY=your_key_here
```

Without a key the AI still works in **demo mode** with smart fallback answers.

## Project Structure

```
restaurant_ai/
├── apps/
│   ├── accounts/      # Custom User + Roles
│   ├── menu/          # Categories, Items, Variants
│   ├── inventory/     # Ingredients, Recipes
│   ├── orders/        # Tables, Orders, OrderItems
│   ├── kitchen/       # Kitchen tickets
│   ├── staff/         # Shifts
│   ├── customers/     # CRM + Loyalty
│   ├── analytics/     # Dashboard
│   └── ai_agent/      # AI Chat + Services
├── templates/         # Modern Tailwind templates
├── static/
├── config/            # Settings & URLs
└── manage.py
```

## Next Steps You Can Build

- Full interactive POS (add to cart, place order)
- Real-time Kitchen updates (Django Channels / WebSockets)
- Order status change buttons working end-to-end
- Customer loyalty points automation
- Charts (Chart.js) on dashboard
- Multi-location support
- Advanced AI tools (function calling for reports)

## License

MIT – feel free to use and extend.
