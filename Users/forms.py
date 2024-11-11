from typing import Any
from django import forms # type: ignore
from django.contrib.auth.forms import UserCreationForm # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from django.core.exceptions import ValidationError # type: ignore
from django.contrib.auth import authenticate # type: ignore

User = get_user_model()

class UserSignupForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('first_name','last_name','email','password1','password2')

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise ValidationError('Last name is required.')
        return last_name
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError('Email is required.')
        
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already in use.')
        
        return email
    
    def save(self, commit= True):
        user = super(UserSignupForm,self).save(commit=False)
        user.emal = self.cleaned_data['email']
        if commit:
            user.save()
        return user


    

class UserLoginForm(forms.Form):
    email = forms.EmailField(required=False ,widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email',
        'onfocus': "this.placeholder = ''",
        'onblur': "this.placeholder = 'Email'"
    }))
    password = forms.CharField(required=False,widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'onfocus': "this.placeholder = ''",
        'onblur': "this.placeholder = 'Password'"
    }))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if not email:
            self.add_error('email', "Email is required")
        if not password:
            self.add_error('password', "Password is required")

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise ValidationError("Invalid email or password")
        
        return cleaned_data
    
