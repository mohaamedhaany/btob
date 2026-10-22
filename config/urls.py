from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('b2b_orders.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# تخصيص واجهة الإدارة
admin.site.site_header = "بوابة إدارة نظام طلبات المقاهي والمطاعم B2B"
admin.site.site_title = "لوحة التحكم B2B"
admin.site.index_title = "إدارة المنظومة والحسابات"
