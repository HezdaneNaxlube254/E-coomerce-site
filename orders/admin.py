from django.contrib import admin
from .models import Order, OrderItem, OrderAuditLog


class OrderItemInline(admin.TabularInline):
    """Inline for OrderItems in Order admin."""
    
    model = OrderItem
    extra = 1
    readonly_fields = ('total_price',)
    fields = ('product', 'quantity', 'unit_price', 'total_price')


class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""
    
    list_display = ('order_number', 'customer_name', 'status', 'total_amount', 'created_at', 'created_by')
    list_filter = ('status', 'created_at', 'created_by')
    search_fields = ('order_number', 'customer_name', 'customer_email')
    readonly_fields = ('order_number', 'total_amount', 'tax_amount', 'discount_amount', 'final_amount',
                      'created_at', 'updated_at', 'completed_at', 'created_by', 'assigned_to')
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'status', 'created_by', 'assigned_to')
        }),
        ('Customer Info', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_address')
        }),
        ('Financials', {
            'fields': ('total_amount', 'tax_amount', 'discount_amount', 'final_amount'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    inlines = [OrderItemInline]
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class OrderAuditLogAdmin(admin.ModelAdmin):
    """Admin for OrderAuditLog model."""
    
    list_display = ('order', 'action', 'user', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('order__order_number', 'details')
    readonly_fields = ('order', 'user', 'action', 'details', 'timestamp')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderAuditLog, OrderAuditLogAdmin)
admin.site.register(OrderItem)
