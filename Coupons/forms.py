from django import forms
from .models import Coupon


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'description', 'discount_amount', 'discount_type', 'valid_from', 'valid_to', 'is_active', 'max_uses']
        widgets = {
            'valid_from' : forms.DateTimeInput(attrs={'type' : 'datetime-local'}),
            'valid_to' : forms.DateTimeInput(attrs={'type' : 'datetime-local'})
        }