from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.NumberInput(
                attrs={
                    'class': 'rating-input',
                    'min': 1,
                    'max': 5,
                    'required': True
                }
            ),
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Review Title (optional)',
                }
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Write your review here...',
                    'required': True
                }
            )
        }

    def clean(self):
        cleaned_data = super().clean()
        if len(cleaned_data.get('comment', '')) < 10:
            raise forms.ValidationError("Review comment must be at least 10 characters long")
        return cleaned_data
