"""URL configuration for products app."""

from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Products
    path('', views.ProductListView.as_view(), name='list'),
    path('<uuid:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('create/', views.ProductCreateView.as_view(), name='create'),
    path('<uuid:pk>/edit/', views.ProductUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', views.ProductDeleteView.as_view(), name='delete'),
    path('<uuid:pk>/restock/', views.restock_product, name='restock'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
]
