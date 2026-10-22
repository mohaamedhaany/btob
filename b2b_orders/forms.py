from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser, RestaurantProfile, CafeProfile, Category, MenuItem, Order


class CustomUserCreationForm(UserCreationForm):
    """
    نموذج إنشاء مستخدم جديد عبر لوحة تحكم الإدارة مع اختيار الدور
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'is_active', 'is_staff')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class CustomUserChangeForm(UserChangeForm):
    """
    نموذج تعديل مستخدم
    """
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'is_active', 'is_staff')


class StyledLoginForm(AuthenticationForm):
    """
    نموذج تسجيل الدخول بتنسيق عصري
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'اسم المستخدم أو البريد',
            'autofocus': True
        }),
        label="اسم المستخدم"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '••••••••'
        }),
        label="كلمة المرور"
    )


class RestaurantProfileForm(forms.ModelForm):
    """
    نموذج تعديل بيانات وشعار المطعم
    """
    class Meta:
        model = RestaurantProfile
        fields = ['name', 'description', 'phone', 'address', 'logo', 'cover_image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: شاورما ومشاوي الأصالة'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'نبذة مختصرة عن أطباقكم وتخصصكم...'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05xxxxxxxx'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة، الحي، الشارع'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CafeProfileForm(forms.ModelForm):
    """
    نموذج تعديل بيانات الكافيه
    """
    class Meta:
        model = CafeProfile
        fields = ['name', 'phone', 'address', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: مقهى الأصدقاء'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05xxxxxxxx'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدينة، الحي'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class CategoryForm(forms.ModelForm):
    """
    نموذج إنشاء وتعديل أقسام المنيو
    """
    class Meta:
        model = Category
        fields = ['name', 'icon', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: مشويات، سندوتشات، مشروبات...'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-cup-hot'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MenuItemForm(forms.ModelForm):
    """
    نموذج إضافة وتعديل صنف في القائمة
    """
    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'description', 'price', 'image', 'preparation_time', 'is_available']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: برجر دجاج مقرمش'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'المكونات، الإضافات...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25', 'min': '0'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'preparation_time': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, restaurant, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إظهار فقط التصنيفات التابعة لهذا المطعم
        self.fields['category'].queryset = Category.objects.filter(restaurant=restaurant)
