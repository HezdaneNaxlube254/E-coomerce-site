"""
Forms for order management.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Order, OrderItem
from products.models import Product


class OrderForm(forms.ModelForm):
    """Form for Order model."""
    
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phone', 
            'customer_address', 'status', 'notes', 'assigned_to'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit assigned_to to staff users
        from users.models import User
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        
        # Don't allow changing status to certain values if order is completed
        if self.instance and self.instance.is_completed:
            self.fields['status'].disabled = True
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate status transitions
        if self.instance and self.instance.pk:
            old_status = self.instance.status
            new_status = cleaned_data.get('status')
            
            if old_status != new_status:
                allowed_transitions = {
                    'draft': ['pending', 'cancelled'],
                    'pending': ['processing', 'cancelled'],
                    'processing': ['shipped', 'cancelled'],
                    'shipped': ['delivered'],
                    'delivered': [],
                    'cancelled': [],
                }
                
                if new_status not in allowed_transitions.get(old_status, []):
                    raise ValidationError(
                        f'Cannot transition from {old_status} to {new_status}.'
                    )
        
        return cleaned_data


class OrderItemForm(forms.ModelForm):
    """Form for OrderItem model."""
    
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(status='active'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1000
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        
        if product and quantity:
            if product.quantity < quantity:
                raise ValidationError(
                    f'Insufficient stock. Available: {product.quantity}'
                )
        
        return cleaned_data
