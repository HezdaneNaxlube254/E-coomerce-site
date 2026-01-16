"""
Order models for the ecommerce system.
"""

import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
from products.models import Product


class Order(models.Model):
    """Order model."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders_created')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_assigned')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['created_at']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number}"
    
    def save(self, *args, **kwargs):
        """Generate order number on creation."""
        if not self.order_number:
            timestamp = timezone.now().strftime('%Y%m%d')
            last_order = Order.objects.filter(order_number__contains=timestamp).order_by('-created_at').first()
            
            if last_order:
                try:
                    last_number = int(last_order.order_number[-4:])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.order_number = f"ORD-{timestamp}-{new_number:04d}"
        
        # Update final amount
        self.final_amount = self.total_amount + self.tax_amount - self.discount_amount
        
        # Set completed_at for delivered/cancelled orders
        if self.status in ['delivered', 'cancelled'] and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate order status transitions."""
        if self.pk:
            old_order = Order.objects.get(pk=self.pk)
            
            # Define allowed status transitions
            allowed_transitions = {
                'draft': ['pending', 'cancelled'],
                'pending': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered'],
                'delivered': [],  # Final state
                'cancelled': [],  # Final state
            }
            
            if old_order.status != self.status:
                if self.status not in allowed_transitions.get(old_order.status, []):
                    raise ValidationError(
                        f'Cannot transition from {old_order.status} to {self.status}. '
                        f'Allowed transitions: {allowed_transitions.get(old_order.status, [])}'
                    )
    
    @property
    def can_be_modified(self):
        """Check if order can be modified."""
        return self.status in ['draft', 'pending']
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.status in ['draft', 'pending', 'processing']
    
    @property
    def is_completed(self):
        """Check if order is completed."""
        return self.status in ['delivered', 'cancelled']
    
    def update_totals(self):
        """Update order totals from items."""
        items = self.items.all()
        self.total_amount = sum(item.total_price for item in items)
        self.save()
    
    def cancel_order(self, user, reason=''):
        """Cancel the order with validation."""
        if not self.can_be_cancelled:
            raise ValidationError('Order cannot be cancelled in its current status.')
        
        self.status = 'cancelled'
        self.notes = f"{self.notes}\n\nCancelled by {user.email}: {reason}"
        self.save()
        
        # Restore product quantities
        for item in self.items.all():
            try:
                product = item.product
                product.quantity += item.quantity
                product.save()
            except Product.DoesNotExist:
                pass  # Product no longer exists
    
    def process_order(self, user):
        """Process the order (move from pending to processing)."""
        if self.status != 'pending':
            raise ValidationError('Only pending orders can be processed.')
        
        # Validate stock availability
        for item in self.items.all():
            if item.quantity > item.product.quantity:
                raise ValidationError(
                    f'Insufficient stock for {item.product.name}. '
                    f'Available: {item.product.quantity}, Requested: {item.quantity}'
                )
        
        # Deduct stock
        for item in self.items.all():
            item.product.decrement_quantity(item.quantity)
        
        self.status = 'processing'
        self.assigned_to = user
        self.save()


class OrderItem(models.Model):
    """Order item model."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    class Meta:
        unique_together = ['order', 'product']
        indexes = [
            models.Index(fields=['order', 'product']),
        ]
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Calculate total price."""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update order totals
        self.order.update_totals()
    
    def delete(self, *args, **kwargs):
        """Update order totals on deletion."""
        order = self.order
        super().delete(*args, **kwargs)
        order.update_totals()


class OrderAuditLog(models.Model):
    """Audit log for order changes."""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('status_change', 'Status Change'),
        ('add_item', 'Add Item'),
        ('remove_item', 'Remove Item'),
        ('cancel', 'Cancel'),
        ('process', 'Process'),
        ('ship', 'Ship'),
        ('deliver', 'Deliver'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['order', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Order {self.order.order_number} - {self.action} - {self.timestamp}"
