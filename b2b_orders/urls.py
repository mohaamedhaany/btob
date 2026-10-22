from django.urls import path
from . import views

urlpatterns = [
    # المصادقة والتوجيه
    path('', views.dashboard_redirect, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.dashboard_redirect, name='dashboard_redirect'),

    # واجهات وصلاحيات المطعم (Restaurant Portal)
    path('restaurant/dashboard/', views.restaurant_dashboard, name='restaurant_dashboard'),
    path('restaurant/profile/', views.restaurant_profile_view, name='restaurant_profile'),
    
    # إدارة الفئات
    path('restaurant/categories/', views.category_list_view, name='restaurant_categories'),
    path('restaurant/categories/<int:pk>/edit/', views.category_edit_view, name='category_edit'),
    path('restaurant/categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),

    # إدارة قائمة الطعام (Menu Items)
    path('restaurant/menu/', views.menu_item_list_view, name='restaurant_menu_list'),
    path('restaurant/menu/create/', views.menu_item_create_view, name='menu_item_create'),
    path('restaurant/menu/<int:pk>/edit/', views.menu_item_edit_view, name='menu_item_edit'),
    path('restaurant/menu/<int:pk>/delete/', views.menu_item_delete_view, name='menu_item_delete'),
    path('restaurant/menu/<int:pk>/toggle/', views.menu_item_toggle_availability, name='menu_item_toggle'),

    # شاشة الطلبات الواردة للمطعم
    path('restaurant/orders/', views.restaurant_orders_view, name='restaurant_orders'),
    path('restaurant/orders/<int:pk>/status/', views.restaurant_update_order_status, name='restaurant_update_order_status'),
    path('restaurant/api/live-orders/', views.restaurant_live_orders_api, name='restaurant_live_orders_api'),

    # واجهات وصلاحيات الكافيه (Cafe Portal)
    path('cafe/dashboard/', views.cafe_dashboard, name='cafe_dashboard'),
    path('cafe/restaurant/<int:restaurant_id>/', views.cafe_restaurant_menu, name='cafe_restaurant_menu'),
    path('cafe/order/place/', views.cafe_place_order, name='cafe_place_order'),
    path('cafe/orders/', views.cafe_orders_history, name='cafe_orders_history'),
    path('cafe/orders/<int:pk>/', views.cafe_order_detail, name='cafe_order_detail'),
]
