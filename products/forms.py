"""
Forms for product management.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category


class CategoryForm(forms.ModelForm):
    """Form for Category model."""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    """Form for Product model."""
    
    audit_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes about this change...'
        }),
        help_text='Add notes about changes for audit purposes'
    )
    
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'description', 'category', 
            'price', 'cost', 'quantity', 'min_quantity', 'max_quantity',
            'image', 'status'
        ]
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (2MB limit)
            if image.size > 2 * 1024 * 1024:
                raise ValidationError('Image file size must be under 2MB.')
            
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png']
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError('Only JPG and PNG images are allowed.')
        
        return image
    
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        cost = cleaned_data.get('cost')
        
        if price and cost and price < cost:
            self.add_error('price', 'Price must be greater than or equal to cost.')
        
        return cleaned_data
