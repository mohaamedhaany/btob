from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def restaurant_required(view_func):
    """
    مُزخرف (Decorator) للتحقق من أن المستخدم المسجل هو صاحب مطعم (أو مشرف عام)
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.role == 'RESTAURANT':
            # تأكد من وجود ملف المطعم وإنشائه تلقائياً إذا لزم الأمر
            request.user.get_or_create_restaurant_profile()
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'غير مصرح لك بالدخول إلى لوحة تحكم المطعم.')
        return redirect('cafe_dashboard')
    
    return _wrapped_view


def cafe_required(view_func):
    """
    مُزخرف (Decorator) للتحقق من أن المستخدم المسجل هو كافيه (أو مشرف عام)
    """
    @wraps(view_func)
    @login_required(login_url='login')
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.role == 'CAFE':
            # تأكد من وجود ملف الكافيه وإنشائه تلقائياً إذا لزم الأمر
            request.user.get_or_create_cafe_profile()
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'غير مصرح لك بالدخول إلى شاشة طلبات الكافيه.')
        return redirect('restaurant_dashboard')
    
    return _wrapped_view
