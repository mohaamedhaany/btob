from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import RestaurantProfile, CafeProfile, Category, MenuItem, Order, OrderItem

User = get_user_model()


class B2BOrderingSystemTests(TestCase):
    def setUp(self):
        self.client = Client()

        # 1. Superuser
        self.admin = User.objects.create_superuser(
            username='test_admin',
            email='admin@test.com',
            password='password123',
            role='ADMIN'
        )

        # 2. Restaurant User
        self.restaurant_user = User.objects.create_user(
            username='test_rest',
            password='password123',
            role='RESTAURANT',
            first_name='مطعم التجربة'
        )
        self.restaurant = self.restaurant_user.restaurant_profile
        self.restaurant.name = 'مطعم المشويات التجريبي'
        self.restaurant.save()

        # Category and MenuItem
        self.category = Category.objects.create(
            restaurant=self.restaurant,
            name='مشويات'
        )
        self.menu_item = MenuItem.objects.create(
            restaurant=self.restaurant,
            category=self.category,
            name='كباب لحم',
            price=Decimal('50.00'),
            is_available=True
        )

        # 3. Cafe User
        self.cafe_user = User.objects.create_user(
            username='test_cafe',
            password='password123',
            role='CAFE',
            first_name='كافيه التجربة'
        )
        self.cafe = self.cafe_user.cafe_profile
        self.cafe.name = 'كافيه الأمل التجريبي'
        self.cafe.save()

    def test_user_roles(self):
        """التحقق من صحة خصائص الأدوار والإشارات التلقائية"""
        self.assertTrue(self.restaurant_user.is_restaurant)
        self.assertFalse(self.restaurant_user.is_cafe)
        self.assertTrue(self.cafe_user.is_cafe)
        self.assertFalse(self.cafe_user.is_restaurant)

        self.assertIsNotNone(self.restaurant_user.restaurant_profile)
        self.assertIsNotNone(self.cafe_user.cafe_profile)

    def test_login_redirection(self):
        """التحقق من توجيه كل مستخدم تلقائياً حسب دوره"""
        # Restaurant Login
        self.client.login(username='test_rest', password='password123')
        response = self.client.get(reverse('dashboard_redirect'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('restaurant_dashboard'))
        self.client.logout()

        # Cafe Login
        self.client.login(username='test_cafe', password='password123')
        response = self.client.get(reverse('dashboard_redirect'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cafe_dashboard'))
        self.client.logout()

    def test_access_control(self):
        """التحقق من حظر الكافيه عن لوحة المطعم والعكس"""
        # Cafe trying to access restaurant dashboard -> redirected
        self.client.login(username='test_cafe', password='password123')
        response = self.client.get(reverse('restaurant_dashboard'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('cafe_dashboard'))
        self.client.logout()

        # Restaurant trying to access cafe dashboard -> redirected
        self.client.login(username='test_rest', password='password123')
        response = self.client.get(reverse('cafe_dashboard'), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('restaurant_dashboard'))
        self.client.logout()

    def test_admin_access_both_dashboards_safely(self):
        """التحقق من أن المشرف العام يستطيع فتح لوحة الكافيه ولوحة المطعم دون خطأ RelatedObjectDoesNotExist"""
        self.client.login(username='test_admin', password='password123')
        
        # Admin visits cafe dashboard
        response_cafe = self.client.get(reverse('cafe_dashboard'))
        self.assertEqual(response_cafe.status_code, 200)
        
        # Admin visits restaurant dashboard
        response_rest = self.client.get(reverse('restaurant_dashboard'))
        self.assertEqual(response_rest.status_code, 200)

    def test_admin_portal_dashboard(self):
        """التحقق من لوحة الإدارة التنفيذية ورؤية المشرف لبيانات الملاك والمطاعم"""
        self.client.login(username='test_admin', password='password123')
        response = self.client.get(reverse('admin_portal_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'لوحة الإدارة التنفيذية')
        self.assertContains(response, self.restaurant.name)
        self.assertContains(response, self.cafe.name)

        # Non-superusers cannot access
        self.client.login(username='test_cafe', password='password123')
        response = self.client.get(reverse('admin_portal_dashboard'), follow=False)
        self.assertEqual(response.status_code, 302)

    def test_admin_portal_quick_create_user(self):
        """التحقق من إنشاء حساب مطعم جديد عبر لوحة الإدارة التنفيذية"""
        self.client.login(username='test_admin', password='password123')
        payload = {
            'create_user': '1',
            'role': 'RESTAURANT',
            'business_name': 'مطعم الشام الأصيل',
            'business_phone': '0559988776',
            'business_address': 'الرياض',
            'first_name': 'خالد',
            'last_name': 'العمري',
            'phone_number': '0501122334',
            'username': 'sham_restaurant',
            'email': 'sham@test.com',
            'password': 'password123'
        }
        response = self.client.post(reverse('admin_portal_dashboard'), data=payload, follow=True)
        self.assertEqual(response.status_code, 200)

        new_user = User.objects.get(username='sham_restaurant')
        self.assertEqual(new_user.role, 'RESTAURANT')
        self.assertEqual(new_user.restaurant_profile.name, 'مطعم الشام الأصيل')
        self.assertEqual(new_user.phone_number, '0501122334')
        self.assertEqual(new_user.restaurant_profile.phone, '0559988776')

    def test_admin_toggle_restaurant_status(self):
        """التحقق من إمكانية تغيير حالة المطعم من لوحة المشرف"""
        self.client.login(username='test_admin', password='password123')
        initial_status = self.restaurant.is_active
        response = self.client.post(reverse('admin_toggle_restaurant_status', kwargs={'pk': self.restaurant.id}))
        self.assertEqual(response.status_code, 302)

        self.restaurant.refresh_from_db()
        self.assertNotEqual(self.restaurant.is_active, initial_status)

    def test_cafe_place_order_api(self):
        """التحقق من إنشاء طلب B2B من الكافيه وحساب الإجمالي وبنود الطلب"""
        self.client.login(username='test_cafe', password='password123')

        payload = {
            'restaurant_id': self.restaurant.id,
            'table_or_customer': 'طاولة 3',
            'customer_notes': 'بدون بصل',
            'items': [
                {
                    'item_id': self.menu_item.id,
                    'quantity': 3,
                    'notes': 'مستوي زيادة'
                }
            ]
        }

        response = self.client.post(
            reverse('cafe_place_order'),
            data=payload,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        # Verify DB Order
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.cafe, self.cafe)
        self.assertEqual(order.restaurant, self.restaurant)
        self.assertEqual(order.status, 'PENDING')
        self.assertEqual(order.total_price, Decimal('150.00')) # 50 * 3
        self.assertEqual(order.items.count(), 1)

        item = order.items.first()
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.subtotal, Decimal('150.00'))

    def test_restaurant_update_order_status(self):
        """التحقق من تحديث حالة الطلب من قبل المطعم"""
        order = Order.objects.create(
            cafe=self.cafe,
            restaurant=self.restaurant,
            status='PENDING',
            total_price=Decimal('50.00')
        )

        self.client.login(username='test_rest', password='password123')

        # Update to ACCEPTED
        response = self.client.post(
            reverse('restaurant_update_order_status', kwargs={'pk': order.id}),
            data={'status': 'ACCEPTED'}
        )
        self.assertEqual(response.status_code, 302)

        order.refresh_from_db()
        self.assertEqual(order.status, 'ACCEPTED')
