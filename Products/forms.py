from django import forms
from django.forms import inlineformset_factory
from .models import Product, ProductVariant

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'image1', 'image2', 'image3', 'status', 'offer_type', 'offer_value', 'offer_start_date', 'offer_end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Product Description', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control scrollable-select'}),
            'image1': forms.ClearableFileInput(attrs={'class': 'form-control-file image-input'}),
            'image2': forms.ClearableFileInput(attrs={'class': 'form-control-file image-input'}),
            'image3': forms.ClearableFileInput(attrs={'class': 'form-control-file image-input'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'offer_type': forms.Select(attrs={'class': 'form-control'}),
            'offer_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'offer_start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'offer_end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['image1', 'image2', 'image3']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})
            else:
                self.fields[field].widget.attrs.update({'class': 'form-control-file image-input'})
        self.fields['category'].widget.attrs.update({'class': 'form-control scrollable-select'})

    def clean_image1(self):
        return self._clean_image('image1')
    
    def clean_image2(self):
        return self._clean_image('image2')
    
    def clean_image3(self):
        return self._clean_image('image3')
    
    def _clean_image(self, field_image):
        image = self.cleaned_data.get(field_image)
        return image if image else None
    
    
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['size', 'price' , 'stock']

ProductVariantFormSet = inlineformset_factory(Product, ProductVariant, form=ProductVariantForm, extra=1, can_delete=True)