from django.contrib import admin
from .models import Category, Product, ProductAuditLog


class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""
    
    list_display = ('sku', 'name', 'category', 'price', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('sku', 'name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        ('Basic Info', {
            'fields': ('sku', 'name', 'description', 'category', 'image')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'cost', 'quantity', 'min_quantity', 'max_quantity')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Audit Info', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class ProductAuditLogAdmin(admin.ModelAdmin):
    """Admin for ProductAuditLog model."""
    
    list_display = ('product', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('product__sku', 'product__name', 'notes')
    readonly_fields = ('product', 'user', 'action', 'changes', 'notes', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAuditLog, ProductAuditLogAdmin)
