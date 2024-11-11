from typing import Any
from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'status', 'offer_type', 'offer_value', 'offer_start_date', 'offer_end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'offer_type': forms.Select(attrs={'class': 'form-control'}),
            'offer_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'offer_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'offer_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        if Category.objects.filter(name__iexact = name).exclude(pk = self.instance.pk).exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name