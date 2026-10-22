import sys
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from b2b_orders.models import RestaurantProfile, CafeProfile, Category, MenuItem, Order, OrderItem

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed realistic B2B data (restaurants, cafes, menus, sample orders) to Supabase'

    def handle(self, *args, **options):
        self.stdout.write('Starting seeding sample data into Supabase PostgreSQL...')

        # 1. Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@b2bfood.com',
                'first_name': 'Admin',
                'last_name': 'Superuser',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123456')
            admin_user.save()
            self.stdout.write('Created superuser: admin / admin123456')
        else:
            self.stdout.write('Superuser admin already exists.')

        # 2. Restaurant 1: Mashawi Qasr
        rest1_user, created = User.objects.get_or_create(
            username='mashawi_chef',
            defaults={
                'email': 'grill@foodb2b.com',
                'first_name': 'مطعم',
                'last_name': 'قصر المشويات',
                'role': 'RESTAURANT',
                'phone_number': '0551122334',
            }
        )
        if created:
            rest1_user.set_password('rest123456')
            rest1_user.save()

        rest1_profile = rest1_user.restaurant_profile
        rest1_profile.name = 'مطعم قصر المشويات الأصيل'
        rest1_profile.description = 'نخبة أطباق المشويات الحلبية، لحوم نعيمي طازجة يومياً ومقبلات شامية فاخرة.'
        rest1_profile.phone = '0551122334'
        rest1_profile.address = 'الرياض - حي النرجس - طريق أبي بكر الصديق'
        rest1_profile.is_active = True
        rest1_profile.save()

        cat_grills, _ = Category.objects.get_or_create(
            restaurant=rest1_profile,
            name='مشويات على الفحم',
            defaults={'icon': 'bi-fire', 'order': 1}
        )
        cat_appetizers, _ = Category.objects.get_or_create(
            restaurant=rest1_profile,
            name='المقبلات والسلطات',
            defaults={'icon': 'bi-egg-fried', 'order': 2}
        )
        cat_drinks, _ = Category.objects.get_or_create(
            restaurant=rest1_profile,
            name='عصائر طازجة',
            defaults={'icon': 'bi-cup-straw', 'order': 3}
        )

        items_rest1 = [
            (cat_grills, 'أوصال لحم نعيمي مشوي', 'لحم بلدي متبل بخلطة الأصالة ومشوي على الفحم مع خبز البيواز والبصل المشوي', Decimal('58.00'), 20),
            (cat_grills, 'كباب لحم حلبي خاص', 'سيخان كباب لحم طازج مع البقدونس والتوابل والمكسرات', Decimal('48.00'), 15),
            (cat_grills, 'شيش طاووق مدخن', 'قطع صدور دجاج متبلة بالزبادي والليمون والثوم مشوية بعناية', Decimal('42.00'), 15),
            (cat_appetizers, 'حمص باللحمة المفرومة والصنوبر', 'حمص كريمي بزيت الزيتون البكر ولحم مفروم مع صنوبر محمص', Decimal('26.00'), 5),
            (cat_appetizers, 'تبولة شامية بدبس الرمان', 'بقدونس مفروم ناعم، طماطم، برغل ناعم، ليمون ودبس رمان فاخر', Decimal('22.00'), 5),
            (cat_drinks, 'عصير رمان طبيعي طازج', 'رمان طازج معصور 100% بدون إضافة سكر', Decimal('18.00'), 5),
            (cat_drinks, 'عصير ليمون ونعناع مثلج', 'مزيج منعش من الليمون والنعناع الطازج الثلجي', Decimal('15.00'), 5),
        ]
        for cat, name, desc, price, prep in items_rest1:
            MenuItem.objects.get_or_create(
                restaurant=rest1_profile,
                name=name,
                defaults={
                    'category': cat,
                    'description': desc,
                    'price': price,
                    'preparation_time': prep,
                    'is_available': True
                }
            )

        self.stdout.write('Configured Restaurant 1: mashawi_chef / rest123456')

        # 3. Restaurant 2: Burger House
        rest2_user, created = User.objects.get_or_create(
            username='burger_house',
            defaults={
                'email': 'burger@foodb2b.com',
                'first_name': 'مطعم',
                'last_name': 'برجر هاوس',
                'role': 'RESTAURANT',
                'phone_number': '0569988776',
            }
        )
        if created:
            rest2_user.set_password('rest123456')
            rest2_user.save()

        rest2_profile = rest2_user.restaurant_profile
        rest2_profile.name = 'مطعم برجر هاوس & كرسبي'
        rest2_profile.description = 'برجر لحم بلاك أنجوس محمص على الجريل وساندوتشات دجاج مقرمش مميزة.'
        rest2_profile.phone = '0569988776'
        rest2_profile.address = 'الرياض - حي الملقا - طريق أنس بن مالك'
        rest2_profile.is_active = True
        rest2_profile.save()

        cat_burgers, _ = Category.objects.get_or_create(
            restaurant=rest2_profile,
            name='البرجر المميز',
            defaults={'icon': 'bi-bullseye', 'order': 1}
        )
        cat_sides, _ = Category.objects.get_or_create(
            restaurant=rest2_profile,
            name='الأطباق الجانبية',
            defaults={'icon': 'bi-box', 'order': 2}
        )

        items_rest2 = [
            (cat_burgers, 'ترافل أنجوس برجر', 'شريحة أنجوس 150 جرام مع صوص الترافل الفاخر، جبنة سويسرية وفطر مشوح', Decimal('44.00'), 12),
            (cat_burgers, 'كرسبي تشيكن ديناميت', 'صدر دجاج مقلي مقرمش، صوص الديناميت الحار، سلطة كولسلو وخيار مخلل', Decimal('36.00'), 10),
            (cat_burgers, 'سماش كلاسيك دبل', 'شريحتان سماش لحم بقري مع جبن شيدر ذائب وصوص هاوس الخاص', Decimal('39.00'), 10),
            (cat_sides, 'بطاطس مقرمشة بالجبنة والبيكون', 'بطاطس مقلية مغطاة بصلصة الجبن الذائبة وقطع اللحم المقرمش والبصل المقلي', Decimal('24.00'), 8),
            (cat_sides, 'أصابع موزاريلا مقرمشة (5 قطع)', 'أصابع جبنة موزاريلا ذهبية مع صوص المارينارا الإيطالي', Decimal('20.00'), 6),
        ]
        for cat, name, desc, price, prep in items_rest2:
            MenuItem.objects.get_or_create(
                restaurant=rest2_profile,
                name=name,
                defaults={
                    'category': cat,
                    'description': desc,
                    'price': price,
                    'preparation_time': prep,
                    'is_available': True
                }
            )

        self.stdout.write('Configured Restaurant 2: burger_house / rest123456')

        # 4. Cafe 1
        cafe1_user, created = User.objects.get_or_create(
            username='aroma_cafe',
            defaults={
                'email': 'aroma@cafe.com',
                'first_name': 'مقهى',
                'last_name': 'أروما لاونج',
                'role': 'CAFE',
                'phone_number': '0541234567',
            }
        )
        if created:
            cafe1_user.set_password('cafe123456')
            cafe1_user.save()

        cafe1_profile = cafe1_user.cafe_profile
        cafe1_profile.name = 'مقهى أروما لاونج (Aroma Cafe)'
        cafe1_profile.phone = '0541234567'
        cafe1_profile.address = 'الرياض - حي الياسمين'
        cafe1_profile.save()

        # 5. Cafe 2
        cafe2_user, created = User.objects.get_or_create(
            username='friends_cafe',
            defaults={
                'email': 'friends@cafe.com',
                'first_name': 'مقهى ومحمص',
                'last_name': 'الأصدقاء',
                'role': 'CAFE',
                'phone_number': '0597654321',
            }
        )
        if created:
            cafe2_user.set_password('cafe123456')
            cafe2_user.save()

        cafe2_profile = cafe2_user.cafe_profile
        cafe2_profile.name = 'كافيه الأصدقاء (Friends Cafe)'
        cafe2_profile.phone = '0597654321'
        cafe2_profile.address = 'الرياض - حي الصحافة'
        cafe2_profile.save()

        self.stdout.write('Configured Cafes: aroma_cafe & friends_cafe / cafe123456')

        # 6. Sample Live Order
        order_item_sample = MenuItem.objects.filter(restaurant=rest1_profile).first()
        if order_item_sample:
            order, o_created = Order.objects.get_or_create(
                cafe=cafe1_profile,
                restaurant=rest1_profile,
                table_or_customer='طاولة رقم 5 (صالة العائلات)',
                defaults={
                    'customer_notes': 'الرجاء الاستعجال والخبز يكون ساخن جداً وبدون مخلل حار',
                    'status': 'PENDING',
                    'total_price': order_item_sample.price * 2
                }
            )
            if o_created:
                OrderItem.objects.create(
                    order=order,
                    menu_item=order_item_sample,
                    item_name=order_item_sample.name,
                    unit_price=order_item_sample.price,
                    quantity=2,
                    subtotal=order_item_sample.price * 2,
                    notes='بدون مخلل'
                )
                self.stdout.write(f'Created sample live order: {order.order_number}')

        self.stdout.write('====================================================')
        self.stdout.write('Supabase Database seeded successfully!')
        self.stdout.write('User Credentials:')
        self.stdout.write('  Superuser: admin / admin123456')
        self.stdout.write('  Restaurant 1: mashawi_chef / rest123456')
        self.stdout.write('  Restaurant 2: burger_house / rest123456')
        self.stdout.write('  Cafe 1: aroma_cafe / cafe123456')
        self.stdout.write('  Cafe 2: friends_cafe / cafe123456')
        self.stdout.write('====================================================')
