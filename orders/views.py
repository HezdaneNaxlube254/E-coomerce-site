"""
Views for order management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.http import JsonResponse

from .models import Order, OrderItem, OrderAuditLog
from .forms import OrderForm, OrderItemForm
from products.models import Product
from products.permissions import is_admin_or_staff
import json


class OrderListView(LoginRequiredMixin, ListView):
    """List all orders."""
    
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.select_related('created_by', 'assigned_to').prefetch_related('items')
        
        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(customer_email__icontains=search)
            )
        
        # Date range filter
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        
        # Statistics
        context['total_orders'] = Order.objects.count()
        context['pending_orders'] = Order.objects.filter(status='pending').count()
        context['processing_orders'] = Order.objects.filter(status='processing').count()
        
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """View order details."""
    
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.select_related('product')
        context['audit_logs'] = self.object.audit_logs.all()[:10]
        context['can_modify'] = self.object.can_be_modified
        context['can_cancel'] = self.object.can_be_cancelled
        return context


class OrderCreateView(LoginRequiredMixin, CreateView):
    """Create a new order."""
    
    model = Order
    form_class = OrderForm
    template_name = 'orders/form.html'
    success_url = reverse_lazy('orders:list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # Create audit log
        order = form.save()
        OrderAuditLog.objects.create(
            order=order,
            user=self.request.user,
            action='create',
            details={
                'order_number': order.order_number,
                'customer': order.customer_name,
                'status': order.status,
            }
        )
        
        messages.success(self.request, 'Order created successfully. You can now add items.')
        return redirect('orders:detail', pk=order.pk)


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing order."""
    
    model = Order
    form_class = OrderForm
    template_name = 'orders/form.html'
    context_object_name = 'order'
    
    def get_success_url(self):
        return reverse_lazy('orders:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Track changes
        old_order = Order.objects.get(pk=self.object.pk)
        changes = {}
        
        for field in ['customer_name', 'customer_email', 'customer_phone', 'customer_address', 'status']:
            old_value = getattr(old_order, field)
            new_value = form.cleaned_data[field]
            if old_value != new_value:
                changes[field] = {'old': str(old_value), 'new': str(new_value)}
        
        # Special handling for status changes
        if old_order.status != form.cleaned_data['status']:
            OrderAuditLog.objects.create(
                order=self.object,
                user=self.request.user,
                action='status_change',
                details={
                    'from': old_order.status,
                    'to': form.cleaned_data['status'],
                    'changes': changes,
                }
            )
        
        order = form.save()
        
        # Create audit log for other changes
        if changes and old_order.status == form.cleaned_data['status']:
            OrderAuditLog.objects.create(
                order=order,
                user=self.request.user,
                action='update',
                details=changes
            )
        
        messages.success(self.request, 'Order updated successfully.')
        return super().form_valid(form)


@login_required
@user_passes_test(is_admin_or_staff)
def add_order_item(request, pk):
    """Add an item to an order."""
    order = get_object_or_404(Order, pk=pk)
    
    if not order.can_be_modified:
        messages.error(request, 'Cannot modify a completed or cancelled order.')
        return redirect('orders:detail', pk=order.pk)
    
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(pk=product_id)
            
            if product.quantity < quantity:
                messages.error(request, f'Insufficient stock. Available: {product.quantity}')
            else:
                # Check if item already exists
                existing_item = order.items.filter(product=product).first()
                if existing_item:
                    existing_item.quantity += quantity
                    existing_item.save()
                else:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price
                    )
                
                # Create audit log
                OrderAuditLog.objects.create(
                    order=order,
                    user=request.user,
                    action='add_item',
                    details={
                        'product': product.name,
                        'quantity': quantity,
                        'unit_price': str(product.price),
                    }
                )
                
                messages.success(request, f'Added {quantity} x {product.name} to order.')
            
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
@user_passes_test(is_admin_or_staff)
def remove_order_item(request, pk, item_id):
    """Remove an item from an order."""
    order = get_object_or_404(Order, pk=pk)
    
    if not order.can_be_modified:
        messages.error(request, 'Cannot modify a completed or cancelled order.')
        return redirect('orders:detail', pk=order.pk)
    
    try:
        item = OrderItem.objects.get(pk=item_id, order=order)
        
        # Create audit log before deletion
        OrderAuditLog.objects.create(
            order=order,
            user=request.user,
            action='remove_item',
            details={
                'product': item.product.name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
            }
        )
        
        item.delete()
        messages.success(request, 'Item removed from order.')
        
    except OrderItem.DoesNotExist:
        messages.error(request, 'Item not found.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
@user_passes_test(is_admin_or_staff)
def process_order(request, pk):
    """Process an order (move from pending to processing)."""
    order = get_object_or_404(Order, pk=pk)
    
    try:
        order.process_order(request.user)
        
        # Create audit log
        OrderAuditLog.objects.create(
            order=order,
            user=request.user,
            action='process',
            details={'processed_by': request.user.email}
        )
        
        messages.success(request, 'Order is now being processed.')
    except ValidationError as e:
        messages.error(request, str(e))
    
    return redirect('orders:detail', pk=order.pk)


@login_required
@user_passes_test(is_admin_or_staff)
def ship_order(request, pk):
    """Ship an order (move from processing to shipped)."""
    order = get_object_or_404(Order, pk=pk)
    
    if order.status != 'processing':
        messages.error(request, 'Only processing orders can be shipped.')
    else:
        order.status = 'shipped'
        order.save()
        
        # Create audit log
        OrderAuditLog.objects.create(
            order=order,
            user=request.user,
            action='ship',
            details={'shipped_by': request.user.email}
        )
        
        messages.success(request, 'Order marked as shipped.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
@user_passes_test(is_admin_or_staff)
def deliver_order(request, pk):
    """Deliver an order (move from shipped to delivered)."""
    order = get_object_or_404(Order, pk=pk)
    
    if order.status != 'shipped':
        messages.error(request, 'Only shipped orders can be delivered.')
    else:
        order.status = 'delivered'
        order.save()
        
        # Create audit log
        OrderAuditLog.objects.create(
            order=order,
            user=request.user,
            action='deliver',
            details={'delivered_by': request.user.email}
        )
        
        messages.success(request, 'Order marked as delivered.')
    
    return redirect('orders:detail', pk=order.pk)


@login_required
@user_passes_test(is_admin_or_staff)
def cancel_order(request, pk):
    """Cancel an order."""
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        try:
            order.cancel_order(request.user, reason)
            
            # Create audit log
            OrderAuditLog.objects.create(
                order=order,
                user=request.user,
                action='cancel',
                details={'reason': reason}
            )
            
            messages.success(request, 'Order cancelled successfully.')
        except ValidationError as e:
            messages.error(request, str(e))
    
    return redirect('orders:detail', pk=order.pk)


@login_required
def get_product_info(request):
    """Get product information for order form."""
    product_id = request.GET.get('product_id')
    
    try:
        product = Product.objects.get(pk=product_id)
        return JsonResponse({
            'success': True,
            'price': str(product.price),
            'stock': product.quantity,
            'available': product.is_available,
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found.'})


class ExportOrdersView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Export orders to CSV."""
    
    def test_func(self):
        return self.request.user.is_admin
    
    def get(self, request):
        # This would generate a CSV file
        # For now, just return a message
        messages.info(request, 'CSV export functionality will be implemented in production.')
        return redirect('orders:list')
