"""
Views for product management.
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

from .models import Product, Category, ProductAuditLog
from .forms import ProductForm, CategoryForm
from .permissions import is_admin_or_staff


class ProductListView(LoginRequiredMixin, ListView):
    """List all products."""
    
    model = Product
    template_name = 'products/list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category').order_by('-created_at')
        
        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(sku__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Filter by category
        category = self.request.GET.get('category', '')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by status
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['status_choices'] = Product.STATUS_CHOICES
        context['search'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    """View product details."""
    
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['audit_logs'] = self.object.audit_logs.all()[:10]
        return context


class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new product."""
    
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    success_url = reverse_lazy('products:list')
    
    def test_func(self):
        return is_admin_or_staff(self.request.user)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # Create audit log
        product = form.save()
        ProductAuditLog.objects.create(
            product=product,
            user=self.request.user,
            action='create',
            changes={
                'sku': product.sku,
                'name': product.name,
                'price': str(product.price),
                'quantity': product.quantity,
            }
        )
        
        messages.success(self.request, 'Product created successfully.')
        return super().form_valid(form)


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing product."""
    
    model = Product
    form_class = ProductForm
    template_name = 'products/form.html'
    context_object_name = 'product'
    
    def test_func(self):
        return is_admin_or_staff(self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('products:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Track changes
        old_product = Product.objects.get(pk=self.object.pk)
        changes = {}
        
        for field in ['sku', 'name', 'price', 'quantity', 'status']:
            old_value = getattr(old_product, field)
            new_value = form.cleaned_data[field]
            if old_value != new_value:
                changes[field] = {'old': str(old_value), 'new': str(new_value)}
        
        form.instance.updated_by = self.request.user
        product = form.save()
        
        # Create audit log if there were changes
        if changes:
            ProductAuditLog.objects.create(
                product=product,
                user=self.request.user,
                action='update',
                changes=changes,
                notes=form.cleaned_data.get('audit_notes', '')
            )
        
        messages.success(self.request, 'Product updated successfully.')
        return super().form_valid(form)


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a product."""
    
    model = Product
    template_name = 'products/confirm_delete.html'
    success_url = reverse_lazy('products:list')
    context_object_name = 'product'
    
    def test_func(self):
        return self.request.user.is_admin
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        
        # Create audit log before deletion
        ProductAuditLog.objects.create(
            product=product,
            user=request.user,
            action='delete',
            changes={
                'sku': product.sku,
                'name': product.name,
            }
        )
        
        messages.success(request, 'Product deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
@user_passes_test(is_admin_or_staff)
def restock_product(request, pk):
    """Restock a product."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0.')
        else:
            old_quantity = product.quantity
            product.quantity += quantity
            
            if product.status == 'out_of_stock' and product.quantity > 0:
                product.status = 'active'
            
            product.save()
            
            # Create audit log
            ProductAuditLog.objects.create(
                product=product,
                user=request.user,
                action='restock',
                changes={
                    'old_quantity': old_quantity,
                    'added_quantity': quantity,
                    'new_quantity': product.quantity,
                },
                notes=request.POST.get('notes', '')
            )
            
            messages.success(request, f'Product restocked successfully. New quantity: {product.quantity}')
            return redirect('products:detail', pk=product.pk)
    
    return render(request, 'products/restock.html', {'product': product})


class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories."""
    
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new category."""
    
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')
    
    def test_func(self):
        return is_admin_or_staff(self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully.')
        return super().form_valid(form)
