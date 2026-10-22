import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    CustomUser,
    RestaurantProfile,
    CafeProfile,
    Category,
    MenuItem,
    Order,
    OrderItem
)
from .forms import (
    StyledLoginForm,
    RestaurantProfileForm,
    CafeProfileForm,
    CategoryForm,
    MenuItemForm
)
from .decorators import restaurant_required, cafe_required


# ==============================================================================
# Authentication & Role Routing
# ==============================================================================

def login_view(request):
    """
    تسجيل الدخول الموحد وتوجيه المستخدم تلقائياً حسب نوع حسابه
    """
    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == 'POST':
        form = StyledLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'مرحباً بك {user.get_full_name() or user.username}!')
            return redirect('dashboard_redirect')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
    else:
        form = StyledLoginForm()

    return render(request, 'auth/login.html', {'form': form})


@login_required(login_url='login')
def dashboard_redirect(request):
    """
    توجيه تلقائي ذكي بعد تسجيل الدخول حسب نوع الحساب
    """
    user = request.user
    if user.is_superuser:
        if user.role == 'RESTAURANT':
            return redirect('restaurant_dashboard')
        elif user.role == 'CAFE':
            return redirect('cafe_dashboard')
        # إذا كان مشرفاً عاماً بدون تحديد، نوجهه إلى لوحة الكافيه كبوابة استعراض أو لوحة الأدمن
        return redirect('cafe_dashboard')
    elif user.role == 'RESTAURANT':
        return redirect('restaurant_dashboard')
    elif user.role == 'CAFE':
        return redirect('cafe_dashboard')
    else:
        return redirect('admin:index')


def logout_view(request):
    """
    تسجيل الخروج
    """
    logout(request)
    messages.info(request, 'تم تسجيل الخروج بنجاح.')
    return redirect('login')


# ==============================================================================
# Restaurant Views (صلاحيات وواجهات المطعم)
# ==============================================================================

@restaurant_required
def restaurant_dashboard(request):
    """
    لوحة تحكم المطعم: إحصائيات سريعة، الطلبات اليومية، والطلبات الواردة حديثاً
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    today = timezone.now().date()

    # إحصائيات
    today_orders = Order.objects.filter(restaurant=restaurant, created_at__date=today)
    pending_orders_count = Order.objects.filter(restaurant=restaurant, status='PENDING').count()
    in_progress_count = Order.objects.filter(restaurant=restaurant, status='ACCEPTED').count()
    completed_today_count = today_orders.filter(status='COMPLETED').count()
    today_revenue = today_orders.filter(status__in=['ACCEPTED', 'READY', 'COMPLETED']).aggregate(
        total=Sum('total_price')
    )['total'] or Decimal('0.00')

    # آخر 6 طلبات واردة
    recent_orders = Order.objects.filter(restaurant=restaurant).select_related('cafe').order_by('-created_at')[:6]
    total_menu_items = restaurant.menu_items.count()

    context = {
        'restaurant': restaurant,
        'pending_orders_count': pending_orders_count,
        'in_progress_count': in_progress_count,
        'completed_today_count': completed_today_count,
        'today_revenue': today_revenue,
        'total_menu_items': total_menu_items,
        'recent_orders': recent_orders,
    }
    return render(request, 'restaurant/dashboard.html', context)


@restaurant_required
def restaurant_profile_view(request):
    """
    إعداد الملف الشخصي ورفع شعار المطعم وغلافه
    """
    restaurant = request.user.get_or_create_restaurant_profile()

    if request.method == 'POST':
        form = RestaurantProfileForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات وشعار المطعم بنجاح!')
            return redirect('restaurant_profile')
        else:
            messages.error(request, 'يرجى مراجعة البيانات المدخلة وتصحيح الأخطاء.')
    else:
        form = RestaurantProfileForm(instance=restaurant)

    return render(request, 'restaurant/profile.html', {
        'restaurant': restaurant,
        'form': form
    })


@restaurant_required
def category_list_view(request):
    """
    عرض وإضافة فئات المنيو (Categories) للمطعم
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    categories = restaurant.categories.annotate(items_count=Count('items')).order_by('order', 'name')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.restaurant = restaurant
            category.save()
            messages.success(request, f'تمت إضافة الفئة "{category.name}" بنجاح.')
            return redirect('restaurant_categories')
    else:
        form = CategoryForm()

    return render(request, 'restaurant/categories.html', {
        'restaurant': restaurant,
        'categories': categories,
        'form': form
    })


@restaurant_required
def category_edit_view(request, pk):
    """
    تعديل فئة موجودة
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    category = get_object_or_404(Category, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل الفئة بنجاح.')
            return redirect('restaurant_categories')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'restaurant/category_edit.html', {
        'restaurant': restaurant,
        'category': category,
        'form': form
    })


@restaurant_required
def category_delete_view(request, pk):
    """
    حذف فئة
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    category = get_object_or_404(Category, pk=pk, restaurant=restaurant)
    if request.method == 'POST':
        cat_name = category.name
        category.delete()
        messages.success(request, f'تم حذف الفئة "{cat_name}".')
    return redirect('restaurant_categories')


@restaurant_required
def menu_item_list_view(request):
    """
    إدارة أصناف المنيو (عرض، تصفية، تفعيل/تعطيل)
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    category_id = request.GET.get('category')
    search_query = request.GET.get('q', '').strip()

    items = MenuItem.objects.filter(restaurant=restaurant).select_related('category')

    if category_id:
        items = items.filter(category_id=category_id)
    if search_query:
        items = items.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))

    categories = restaurant.categories.all()

    return render(request, 'restaurant/menu_list.html', {
        'restaurant': restaurant,
        'items': items,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
    })


@restaurant_required
def menu_item_create_view(request):
    """
    إضافة صنف جديد للقائمة
    """
    restaurant = request.user.get_or_create_restaurant_profile()

    # التأكد من وجود فئات أولاً
    if not restaurant.categories.exists():
        messages.warning(request, 'يجب عليك إضافة فئة واحدة على الأقل قبل إضافة أصناف الطعام.')
        return redirect('restaurant_categories')

    if request.method == 'POST':
        form = MenuItemForm(restaurant, request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = restaurant
            item.save()
            messages.success(request, f'تمت إضافة الصنف "{item.name}" إلى قائمة الطعام بنجاح!')
            return redirect('restaurant_menu_list')
    else:
        form = MenuItemForm(restaurant)

    return render(request, 'restaurant/menu_form.html', {
        'restaurant': restaurant,
        'form': form,
        'title': 'إضافة صنف جديد إلى القائمة',
        'button_text': 'حفظ الصنف'
    })


@restaurant_required
def menu_item_edit_view(request, pk):
    """
    تعديل صنف في قائمة الطعام
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    item = get_object_or_404(MenuItem, pk=pk, restaurant=restaurant)

    if request.method == 'POST':
        form = MenuItemForm(restaurant, request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث بيانات الصنف "{item.name}" بنجاح.')
            return redirect('restaurant_menu_list')
    else:
        form = MenuItemForm(restaurant, instance=item)

    return render(request, 'restaurant/menu_form.html', {
        'restaurant': restaurant,
        'form': form,
        'item': item,
        'title': f'تعديل الصنف: {item.name}',
        'button_text': 'حفظ التعديلات'
    })


@restaurant_required
def menu_item_delete_view(request, pk):
    """
    حذف صنف من قائمة الطعام
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    item = get_object_or_404(MenuItem, pk=pk, restaurant=restaurant)
    if request.method == 'POST':
        item_name = item.name
        item.delete()
        messages.success(request, f'تم حذف الصنف "{item_name}" بنجاح.')
    return redirect('restaurant_menu_list')


@restaurant_required
@require_POST
def menu_item_toggle_availability(request, pk):
    """
    تفعيل أو تعطيل توفر صنف في المنيو بشكل سريع (AJAX)
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    item = get_object_or_404(MenuItem, pk=pk, restaurant=restaurant)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available'])
    return JsonResponse({
        'success': True,
        'is_available': item.is_available,
        'message': f'تمت حالة الصنف إلى: {"متوفر" if item.is_available else "غير متوفر"}'
    })


@restaurant_required
def restaurant_orders_view(request):
    """
    شاشة استقبال وعرض الطلبات الواردة من المقاهي بشكل حيّ ومبسط
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    status_filter = request.GET.get('status', 'ALL')

    orders = Order.objects.filter(restaurant=restaurant).select_related('cafe').prefetch_related('items')

    if status_filter != 'ALL':
        orders = orders.filter(status=status_filter)

    counts = {
        'ALL': Order.objects.filter(restaurant=restaurant).count(),
        'PENDING': Order.objects.filter(restaurant=restaurant, status='PENDING').count(),
        'ACCEPTED': Order.objects.filter(restaurant=restaurant, status='ACCEPTED').count(),
        'READY': Order.objects.filter(restaurant=restaurant, status='READY').count(),
        'COMPLETED': Order.objects.filter(restaurant=restaurant, status='COMPLETED').count(),
        'CANCELLED': Order.objects.filter(restaurant=restaurant, status='CANCELLED').count(),
    }

    return render(request, 'restaurant/orders.html', {
        'restaurant': restaurant,
        'orders': orders,
        'status_filter': status_filter,
        'counts': counts,
    })


@restaurant_required
@require_POST
def restaurant_update_order_status(request, pk):
    """
    تحديث حالة الطلب (قبول، جاهز، تسليم، إلغاء)
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    order = get_object_or_404(Order, pk=pk, restaurant=restaurant)
    new_status = request.POST.get('status')

    valid_statuses = dict(Order.STATUS_CHOICES).keys()
    if new_status in valid_statuses:
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        messages.success(request, f'تم تغيير حالة الطلب {order.order_number} إلى "{order.get_status_display()}".')
    else:
        messages.error(request, 'حالة غير صالحة.')

    # دعم طلبات AJAX أو إعادة التوجيه
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'status': order.status,
            'status_display': order.get_status_display(),
            'badge_class': order.status_badge_class
        })

    return redirect('restaurant_orders')


@restaurant_required
def restaurant_live_orders_api(request):
    """
    نقطة نهاية API لإرجاع عدد الطلبات المعلقة وحالة التحديث للوحة العرض الحية
    """
    restaurant = request.user.get_or_create_restaurant_profile()
    pending_count = Order.objects.filter(restaurant=restaurant, status='PENDING').count()
    active_count = Order.objects.filter(restaurant=restaurant, status__in=['PENDING', 'ACCEPTED', 'READY']).count()

    latest_order = Order.objects.filter(restaurant=restaurant).order_by('-created_at').first()
    latest_order_id = latest_order.id if latest_order else None

    return JsonResponse({
        'pending_count': pending_count,
        'active_count': active_count,
        'latest_order_id': latest_order_id,
        'timestamp': timezone.now().isoformat()
    })


# ==============================================================================
# Cafe Views (صلاحيات وواجهات الكافيه)
# ==============================================================================

@cafe_required
def cafe_dashboard(request):
    """
    شاشة الكافيه الرئيسية: شبكة (Grid) تحتوي على جميع المطاعم المسجلة بشعاراتها وأسمائها
    """
    cafe = request.user.get_or_create_cafe_profile()
    search_query = request.GET.get('q', '').strip()

    restaurants = RestaurantProfile.objects.filter(is_active=True).annotate(
        items_count=Count('menu_items', filter=Q(menu_items__is_available=True))
    )

    if search_query:
        restaurants = restaurants.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query)
        )

    # إحصائية سريعة عن طلبات الكافيه
    orders_count = Order.objects.filter(cafe=cafe).count()
    active_orders_count = Order.objects.filter(cafe=cafe, status__in=['PENDING', 'ACCEPTED', 'READY']).count()

    return render(request, 'cafe/dashboard.html', {
        'cafe': cafe,
        'restaurants': restaurants,
        'search_query': search_query,
        'orders_count': orders_count,
        'active_orders_count': active_orders_count,
    })


@cafe_required
def cafe_restaurant_menu(request, restaurant_id):
    """
    عرض قائمة طعام مطعم محدد بتصميم جذاب Card-based UI مقسم إلى فئات
    مع إمكانية اختيار العناصر وتحديد الكميات وإرسال الطلب
    """
    cafe = request.user.get_or_create_cafe_profile()
    restaurant = get_object_or_404(RestaurantProfile, pk=restaurant_id, is_active=True)

    # جلب الفئات التي تحتوي على أصناف متاحة
    categories = Category.objects.filter(
        restaurant=restaurant,
        is_active=True
    ).prefetch_related(
        'items'
    ).order_by('order', 'name')

    # جلب جميع الأصناف المتاحة
    items = MenuItem.objects.filter(
        restaurant=restaurant,
        is_available=True,
        category__is_active=True
    ).select_related('category')

    return render(request, 'cafe/menu_order.html', {
        'cafe': cafe,
        'restaurant': restaurant,
        'categories': categories,
        'items': items,
    })


@cafe_required
@require_POST
def cafe_place_order(request):
    """
    استقبال طلب الكافيه (عبر JSON أو Form POST) وإنشاء سجل الطلب وبنوده
    """
    cafe = request.user.get_or_create_cafe_profile()

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        # Fallback إذا كان الطلب مُرسلاً كـ standard form-data
        data = request.POST

    restaurant_id = data.get('restaurant_id')
    items_data = data.get('items', [])
    table_or_customer = data.get('table_or_customer', '').strip()
    customer_notes = data.get('customer_notes', '').strip()

    if not restaurant_id:
        return JsonResponse({'success': False, 'message': 'لم يتم تحديد المطعم.'}, status=400)

    restaurant = get_object_or_404(RestaurantProfile, pk=restaurant_id, is_active=True)

    if not items_data or len(items_data) == 0:
        return JsonResponse({'success': False, 'message': 'سلة الطلبات فارغة، يرجى اختيار صنف واحد على الأقل.'}, status=400)

    # التحقق وتجهيز العناصر داخل معالجة ذرية (Atomic Transaction)
    with transaction.atomic():
        order = Order.objects.create(
            cafe=cafe,
            restaurant=restaurant,
            table_or_customer=table_or_customer,
            customer_notes=customer_notes,
            status='PENDING',
            total_price=Decimal('0.00')
        )

        total_amount = Decimal('0.00')

        for item_entry in items_data:
            item_id = item_entry.get('item_id')
            qty = int(item_entry.get('quantity', 1))
            notes = item_entry.get('notes', '')

            if qty <= 0:
                continue

            menu_item = get_object_or_404(MenuItem, pk=item_id, restaurant=restaurant)
            subtotal = menu_item.price * qty

            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                item_name=menu_item.name,
                unit_price=menu_item.price,
                quantity=qty,
                subtotal=subtotal,
                notes=notes
            )
            total_amount += subtotal

        order.total_price = total_amount
        order.save(update_fields=['total_price'])

    return JsonResponse({
        'success': True,
        'message': 'تم إرسال الطلب بنجاح إلى المطعم!',
        'order_number': order.order_number,
        'order_id': order.id,
        'total_price': str(order.total_price),
        'redirect_url': f'/cafe/orders/{order.id}/'
    })


@cafe_required
def cafe_orders_history(request):
    """
    سجل طلبات الكافيه وتتبع حالاتها
    """
    cafe = request.user.get_or_create_cafe_profile()
    status_filter = request.GET.get('status', 'ALL')

    orders = Order.objects.filter(cafe=cafe).select_related('restaurant').prefetch_related('items')

    if status_filter != 'ALL':
        orders = orders.filter(status=status_filter)

    return render(request, 'cafe/orders_history.html', {
        'cafe': cafe,
        'orders': orders,
        'status_filter': status_filter,
    })


@cafe_required
def cafe_order_detail(request, pk):
    """
    تفاصيل الطلب وفاتورة الاستلام الخاصة بالكافيه
    """
    cafe = request.user.get_or_create_cafe_profile()
    order = get_object_or_404(Order, pk=pk, cafe=cafe)

    return render(request, 'cafe/order_detail.html', {
        'cafe': cafe,
        'order': order,
    })
