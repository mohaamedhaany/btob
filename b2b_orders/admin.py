from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, RestaurantProfile, CafeProfile, Category, MenuItem, Order, OrderItem
from .forms import CustomUserCreationForm, CustomUserChangeForm


class RestaurantProfileInline(admin.StackedInline):
    model = RestaurantProfile
    can_delete = False
    verbose_name_plural = 'ملف المطعم المرتبط'
    extra = 0


class CafeProfileInline(admin.StackedInline):
    model = CafeProfile
    can_delete = False
    verbose_name_plural = 'ملف الكافيه المرتبط'
    extra = 0


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    تخصيص لوحة إدارة المستخدمين للإدارة الرئيسية (Superuser)
    """
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'get_role_badge', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('صلاحيات الدور والنظام B2B', {'fields': ('role', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('صلاحيات الدور والنظام B2B', {'fields': ('role', 'phone_number')}),
    )
    search_fields = ['username', 'email', 'phone_number']
    inlines = [RestaurantProfileInline, CafeProfileInline]

    def get_role_badge(self, obj):
        colors = {
            'RESTAURANT': 'background-color: #e3f2fd; color: #0d6efd; padding: 4px 8px; border-radius: 4px;',
            'CAFE': 'background-color: #e8f5e9; color: #198754; padding: 4px 8px; border-radius: 4px;',
            'ADMIN': 'background-color: #fce4ec; color: #d63384; padding: 4px 8px; border-radius: 4px;',
        }
        role_label = dict(CustomUser.ROLE_CHOICES).get(obj.role, obj.role)
        style = colors.get(obj.role, '')
        return format_html('<span style="font-weight: bold; {}">{}</span>', style, role_label)
    get_role_badge.short_description = 'الدور'


@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(admin.ModelAdmin):
    list_display = ['get_logo_preview', 'name', 'user', 'phone', 'is_active', 'active_items_display', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'phone', 'address', 'user__username']

    def get_logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 6px;" />', obj.logo.url)
        return format_html('<span style="color: #999;">بدون شعار</span>')
    get_logo_preview.short_description = 'الشعار'

    def active_items_display(self, obj):
        return obj.menu_items.count()
    active_items_display.short_description = 'عدد الأصناف'


@admin.register(CafeProfile)
class CafeProfileAdmin(admin.ModelAdmin):
    list_display = ['get_logo_preview', 'name', 'user', 'phone', 'address', 'created_at']
    search_fields = ['name', 'phone', 'address', 'user__username']

    def get_logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 6px;" />', obj.logo.url)
        return format_html('<span style="color: #999;">بدون شعار</span>')
    get_logo_preview.short_description = 'الشعار'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'order', 'is_active', 'items_count']
    list_filter = ['restaurant', 'is_active']
    search_fields = ['name', 'restaurant__name']

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'عدد الأصناف'


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['get_image_preview', 'name', 'restaurant', 'category', 'price', 'is_available', 'preparation_time']
    list_filter = ['restaurant', 'category', 'is_available']
    search_fields = ['name', 'description', 'restaurant__name']
    list_editable = ['price', 'is_available']

    def get_image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 45px; height: 45px; object-fit: cover; border-radius: 6px;" />', obj.image.url)
        return format_html('<span style="color: #bbb;">-</span>')
    get_image_preview.short_description = 'الصورة'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['item_name', 'unit_price', 'quantity', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'cafe', 'restaurant', 'table_or_customer', 'total_price', 'get_status_badge', 'created_at']
    list_filter = ['status', 'created_at', 'restaurant', 'cafe']
    search_fields = ['order_number', 'cafe__name', 'restaurant__name', 'table_or_customer']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'total_price']

    def get_status_badge(self, obj):
        colors = {
            'PENDING': '#ffc107',
            'ACCEPTED': '#0d6efd',
            'READY': '#0dcaf0',
            'COMPLETED': '#198754',
            'CANCELLED': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    get_status_badge.short_description = 'الحالة'
