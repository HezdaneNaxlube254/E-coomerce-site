"""
Product models for the ecommerce system.
"""

import uuid
import os
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings


def product_image_path(instance, filename):
    """Generate file path for product image."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('products', filename)


class Category(models.Model):
    """Product category model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    min_quantity = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    max_quantity = models.IntegerField(default=1000, validators=[MinValueValidator(1)])
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='products_created')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='products_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['quantity']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    def clean(self):
        """Validate product data."""
        if self.price < self.cost:
            raise ValidationError('Price must be greater than or equal to cost.')
        
        if self.quantity < 0:
            raise ValidationError('Quantity cannot be negative.')
        
        if self.max_quantity <= self.min_quantity:
            raise ValidationError('Maximum quantity must be greater than minimum quantity.')
    
    @property
    def margin(self):
        """Calculate profit margin."""
        if self.price > 0:
            return ((self.price - self.cost) / self.price) * 100
        return 0
    
    @property
    def needs_restock(self):
        """Check if product needs restocking."""
        return self.quantity <= self.min_quantity
    
    @property
    def is_available(self):
        """Check if product is available for purchase."""
        return self.status == 'active' and self.quantity > 0
    
    def decrement_quantity(self, amount):
        """Decrement product quantity."""
        if amount > self.quantity:
            raise ValidationError(f'Insufficient stock. Available: {self.quantity}')
        
        self.quantity -= amount
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        self.save()


class ProductAuditLog(models.Model):
    """Audit log for product changes."""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('restock', 'Restock'),
        ('price_change', 'Price Change'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changes = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['product', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.product.sku} - {self.action} - {self.timestamp}"
