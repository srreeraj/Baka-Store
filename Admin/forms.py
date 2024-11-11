from typing import Any
from django import forms

class AdminLoginForm(forms.Form):
    email = forms.EmailField(widget = forms.EmailInput(attrs = {
        'class' : 'form-control',
        'placeholder' : 'Admin Mail ID',
        'style' : 'width: 80%;height : 3rem;background-color: #fff3;margin-left :2.2rem;border: 1px solid #ffffff; color : white;'
    }))
    password = forms.CharField(widget= forms.PasswordInput(attrs={
        'class' : 'form-control',
        'placeholder' : 'Password',
        'style' : 'width: 80%;height : 3rem;background-color: #fff3;margin-left :2.2rem;border: 1px solid #ffffff; color: white;'
    }))
