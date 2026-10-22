from django.apps import AppConfig


class B2BOrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'b2b_orders'
    verbose_name = 'نظام طلبات المطاعم والمقاهي B2B'


B2bOrdersConfig = B2BOrdersConfig
