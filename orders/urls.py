"""URL configuration for orders app."""

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Orders
    path('', views.OrderListView.as_view(), name='list'),
    path('<uuid:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('create/', views.OrderCreateView.as_view(), name='create'),
    path('<uuid:pk>/edit/', views.OrderUpdateView.as_view(), name='edit'),
    
    # Order actions
    path('<uuid:pk>/add-item/', views.add_order_item, name='add_item'),
    path('<uuid:pk>/remove-item/<uuid:item_id>/', views.remove_order_item, name='remove_item'),
    path('<uuid:pk>/process/', views.process_order, name='process'),
    path('<uuid:pk>/ship/', views.ship_order, name='ship'),
    path('<uuid:pk>/deliver/', views.deliver_order, name='deliver'),
    path('<uuid:pk>/cancel/', views.cancel_order, name='cancel'),
    
    # API endpoints
    path('api/product-info/', views.get_product_info, name='product_info'),
    
    # Export
    path('export/', views.ExportOrdersView.as_view(), name='export'),
]
