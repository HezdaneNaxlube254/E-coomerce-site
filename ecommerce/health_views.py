from django.views.generic import TemplateView
from django.db import connection
import sys
import django

from products.models import Product
from orders.models import Order
from users.models import User

class HealthView(TemplateView):
    template_name = 'health.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic statistics
        try:
            context['total_products'] = Product.objects.count()
        except:
            context['total_products'] = 0
            
        try:
            context['total_orders'] = Order.objects.count()
        except:
            context['total_orders'] = 0
            
        try:
            context['total_users'] = User.objects.count()
        except:
            context['total_users'] = 0
        
        # System info
        context['python_version'] = sys.version.split()[0]
        context['django_version'] = django.get_version()
        
        return context
