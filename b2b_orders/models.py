import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    مستخدم مخصص للنظام مع تحديد الدور (مطعم أو كافيه أو مدير نظام).
    يتم إنشاء المستخدمين حصراً عن طريق الإدارة (Superuser).
    """
    ROLE_CHOICES = (
        ('RESTAURANT', 'مطعم (Restaurant)'),
        ('CAFE', 'كافيه (Cafe)'),
        ('ADMIN', 'مدير النظام (Admin)'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CAFE',
        verbose_name=_('نوع الحساب / الدور')
    )
    phone_number = models.CharField(
        max_length=25,
        blank=True,
        verbose_name=_('رقم الهاتف للتواصل')
    )

    class Meta:
        verbose_name = _('مستخدم')
        verbose_name_plural = _('المستخدمين')

    @property
    def is_restaurant(self):
        return self.role == 'RESTAURANT'

    @property
    def is_cafe(self):
        return self.role == 'CAFE'

    @property
    def profile(self):
        try:
            if self.is_restaurant:
                return self.get_or_create_restaurant_profile()
            elif self.is_cafe:
                return self.get_or_create_cafe_profile()
        except Exception:
            pass
        return None

    def get_or_create_cafe_profile(self):
        profile, _ = CafeProfile.objects.get_or_create(
            user=self,
            defaults={'name': self.get_full_name() or self.username}
        )
        return profile

    def get_or_create_restaurant_profile(self):
        profile, _ = RestaurantProfile.objects.get_or_create(
            user=self,
            defaults={'name': self.get_full_name() or self.username}
        )
        return profile

    @property
    def cafe_name(self):
        try:
            return self.cafe_profile.name
        except Exception:
            return self.get_full_name() or self.username

    @property
    def restaurant_name(self):
        try:
            return self.restaurant_profile.name
        except Exception:
            return self.get_full_name() or self.username

    def __str__(self):
        role_label = dict(self.ROLE_CHOICES).get(self.role, self.role)
        display_name = self.get_full_name() or self.username
        return f"{display_name} ({role_label})"


class RestaurantProfile(models.Model):
    """
    الملف التعريفي للمطعم: يحتوي على الشعار، الاسم التجاري، العنوان، وأوقات العمل
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='restaurant_profile',
        verbose_name=_('حساب المستخدم')
    )
    name = models.CharField(
        max_length=150,
        verbose_name=_('اسم المطعم')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('نبذة عن المطعم وتخصصه')
    )
    logo = models.ImageField(
        upload_to='restaurants/logos/',
        blank=True,
        null=True,
        verbose_name=_('شعار المطعم (Logo)')
    )
    cover_image = models.ImageField(
        upload_to='restaurants/covers/',
        blank=True,
        null=True,
        verbose_name=_('صورة الغلاف')
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_('رقم هاتف المبيعات / الاستلام')
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('العنوان / الفرع الرئيسي')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('متاح لاستقبال الطلبات حالياً')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الانضمام')
    )

    class Meta:
        verbose_name = _('ملف المطعم')
        verbose_name_plural = _('ملفات المطاعم')
        ordering = ['-created_at']

    def __str__(self):
        return self.name or self.user.username

    @property
    def active_menu_items_count(self):
        return self.menu_items.filter(is_available=True).count()


class CafeProfile(models.Model):
    """
    الملف التعريفي للكافيه: يحتوي على الاسم، الشعار، والفرع
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='cafe_profile',
        verbose_name=_('حساب المستخدم')
    )
    name = models.CharField(
        max_length=150,
        verbose_name=_('اسم الكافيه')
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_('رقم التواصل')
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('موقع / فرع الكافيه')
    )
    logo = models.ImageField(
        upload_to='cafes/logos/',
        blank=True,
        null=True,
        verbose_name=_('شعار الكافيه')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الانضمام')
    )

    class Meta:
        verbose_name = _('ملف الكافيه')
        verbose_name_plural = _('ملفات الكافيهات')
        ordering = ['-created_at']

    def __str__(self):
        return self.name or self.user.username


class Category(models.Model):
    """
    فئات وأقسام قائمة الطعام الخاصة بكل مطعم (مثل: مشويات، مقبلات، مشروبات ساخنة...)
    """
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_('المطعم')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('اسم الفئة / التصنيف')
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        default='bi-tag',
        verbose_name=_('أيقونة التصنيف (Bootstrap Icon)'),
        help_text=_('مثال: bi-cup-hot, bi-egg-fried, bi-cake2, bi-fire')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('ترتيب الظهور')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('نشط ويظهر في القائمة')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإضافة')
    )

    class Meta:
        verbose_name = _('فئة / تصنيف')
        verbose_name_plural = _('فئات قائمة الطعام')
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


class MenuItem(models.Model):
    """
    عناصر قائمة الطعام (الأصناف)
    """
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name=_('المطعم')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('الفئة')
    )
    name = models.CharField(
        max_length=150,
        verbose_name=_('اسم الصنف')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('وصف الصنف ومكوناته')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('السعر (ر.س)')
    )
    image = models.ImageField(
        upload_to='menu_items/',
        blank=True,
        null=True,
        verbose_name=_('صورة الصنف')
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('متاح للطلب الآن')
    )
    preparation_time = models.PositiveIntegerField(
        default=15,
        verbose_name=_('وقت التحضير التقريبي (دقيقة)')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإضافة')
    )

    class Meta:
        verbose_name = _('صنف طعام')
        verbose_name_plural = _('أصناف قائمة الطعام')
        ordering = ['category__order', 'name']

    def __str__(self):
        return f"{self.name} ({self.price} ر.س) - {self.restaurant.name}"


class Order(models.Model):
    """
    الطلب المتبادل بين الكافيه والمطعم
    """
    STATUS_CHOICES = (
        ('PENDING', 'قيد الانتظار'),
        ('ACCEPTED', 'تم القبول / قيد التحضير'),
        ('READY', 'جاهز للتسليم / في الطريق'),
        ('COMPLETED', 'مكتمل ومسلّم'),
        ('CANCELLED', 'ملغي'),
    )

    order_number = models.CharField(
        max_length=40,
        unique=True,
        editable=False,
        verbose_name=_('رقم الطلب')
    )
    cafe = models.ForeignKey(
        CafeProfile,
        on_delete=models.CASCADE,
        related_name='orders_placed',
        verbose_name=_('الكافيه الطالب')
    )
    restaurant = models.ForeignKey(
        RestaurantProfile,
        on_delete=models.CASCADE,
        related_name='orders_received',
        verbose_name=_('المطعم المستقبل')
    )
    table_or_customer = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('رقم الطاولة أو اسم الزبون'),
        help_text=_('مثال: طاولة 5 أو زبون خارجي')
    )
    customer_notes = models.TextField(
        blank=True,
        verbose_name=_('ملاحظات خاصة على الطلب')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name=_('حالة الطلب')
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_('المبلغ الإجمالي (ر.س)')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('وقت الإنشاء')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('آخر تحديث')
    )

    class Meta:
        verbose_name = _('طلب')
        verbose_name_plural = _('الطلبات')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            prefix = "ORD"
            date_str = timezone.now().strftime("%Y%m%d")
            unique_part = uuid.uuid4().hex[:6].upper()
            self.order_number = f"{prefix}-{date_str}-{unique_part}"
        super().save(*args, **kwargs)

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total_price = total
        self.save(update_fields=['total_price'])
        return total

    def __str__(self):
        return f"{self.order_number} - {self.cafe.name} -> {self.restaurant.name}"

    @property
    def status_badge_class(self):
        mapping = {
            'PENDING': 'bg-warning-subtle text-warning border border-warning-subtle',
            'ACCEPTED': 'bg-primary-subtle text-primary border border-primary-subtle',
            'READY': 'bg-info-subtle text-info border border-info-subtle',
            'COMPLETED': 'bg-success-subtle text-success border border-success-subtle',
            'CANCELLED': 'bg-danger-subtle text-danger border border-danger-subtle',
        }
        return mapping.get(self.status, 'bg-light text-muted border')

    @property
    def status_display_ar(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class OrderItem(models.Model):
    """
    عنصر داخل الطلب مع حفظ السعر اللحظي واسم الصنف والكمية
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('الطلب')
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('الصنف الأصلي')
    )
    item_name = models.CharField(
        max_length=150,
        verbose_name=_('اسم الصنف وقت الطلب')
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('سعر الوحدة (ر.س)')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('الكمية')
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('المجموع الفرعي (ر.س)')
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('ملاحظات الصنف')
    )

    class Meta:
        verbose_name = _('عنصر طلب')
        verbose_name_plural = _('عناصر الطلبات')

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.item_name} ({self.subtotal} ر.س)"


# ==============================================================================
# Signals to auto-create RestaurantProfile / CafeProfile when Admin creates User
# ==============================================================================

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    تلقائياً عند إنشاء المستخدم بواسطة الإدارة، نقوم بإنشاء البروفايل الخاص به
    بناءً على الدور المختار.
    """
    if instance.role == 'RESTAURANT':
        RestaurantProfile.objects.get_or_create(
            user=instance,
            defaults={'name': instance.get_full_name() or instance.username}
        )
    elif instance.role == 'CAFE':
        CafeProfile.objects.get_or_create(
            user=instance,
            defaults={'name': instance.get_full_name() or instance.username}
        )
