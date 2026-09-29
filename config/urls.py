from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.analytics import views as analytics_views
from apps.analytics.landing import home as landing_home
from apps.ai_agent import views as ai_views
from apps.orders import views as order_views
from apps.orders import table_views
from apps.menu import views as menu_views
from apps.inventory import views as inventory_views
from apps.accounts import views as accounts_views
from apps.accounts import export_views
from apps.staff import views as staff_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),

    # Public homepage
    path("", landing_home, name="home"),

    # Dashboard (authenticated)
    path("dashboard/", analytics_views.dashboard, name="dashboard"),

    # POS & Orders
    path("pos/", order_views.pos_view, name="pos"),
    path("orders/", order_views.order_list, name="order_list"),
    path("kitchen/", order_views.kitchen_display, name="kitchen"),
    path("api/kitchen/feed/", order_views.kitchen_feed_api, name="api_kitchen_feed"),

    # Tables
    path("tables/", table_views.table_list, name="table_list"),
    path("tables/create/", table_views.table_create, name="table_create"),
    path("api/tables/<int:table_id>/status/", table_views.table_update_status, name="api_table_status"),
    path("tables/<int:table_id>/assign/", table_views.table_assign_waiter, name="table_assign_waiter"),

    # Order APIs
    path("api/orders/create/", order_views.create_order, name="api_create_order"),
    path("api/orders/item/<int:item_id>/status/", order_views.update_item_status, name="api_update_item_status"),
    path("api/orders/<int:order_id>/", order_views.order_detail_api, name="api_order_detail"),
    path("api/orders/<int:order_id>/cancel/", order_views.cancel_order, name="api_cancel_order"),
    path("api/orders/<int:order_id>/edit/", order_views.edit_order, name="api_edit_order"),

    # Menu
    path("menu/", menu_views.menu_list, name="menu_list"),
    path("menu/item/<int:item_id>/toggle/", menu_views.menu_item_toggle, name="menu_item_toggle"),
    path("menu/item/create/", menu_views.menu_item_create, name="menu_item_create"),
    path("menu/category/create/", menu_views.category_create, name="category_create"),

    # Inventory
    path("inventory/", inventory_views.inventory_list, name="inventory_list"),
    path("inventory/adjust/", inventory_views.stock_adjust, name="stock_adjust"),

    # Staff
    path("staff/", staff_views.staff_list, name="staff_list"),
    path("staff/shifts/", staff_views.shift_list, name="shift_list"),
    path("staff/shifts/create/", staff_views.shift_create, name="shift_create"),

    # Accounts / Admin
    path("profile/", accounts_views.profile, name="profile"),
    path("users/", accounts_views.user_list, name="user_list"),
    path("users/<int:user_id>/role/", accounts_views.user_update_role, name="user_update_role"),
    path("activity-logs/", accounts_views.activity_logs, name="activity_logs"),
    path("settings/", accounts_views.settings_view, name="settings"),
    path("export/", export_views.export_page, name="export_page"),
    path("export/orders/", export_views.export_orders_csv, name="export_orders"),
    path("export/inventory/", export_views.export_inventory_csv, name="export_inventory"),
    path("export/menu/", export_views.export_menu_csv, name="export_menu"),
    path("export/backup/", export_views.export_full_backup_json, name="export_backup"),

    # AI Agent
    path("ai/", ai_views.ai_chat, name="ai_chat"),
    path("api/ai/chat/", ai_views.api_chat, name="api_ai_chat"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
