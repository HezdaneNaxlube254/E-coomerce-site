"""
Tests for products views.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from faker import Faker

from products.models import Category, Product

fake = Faker()


class ProductListViewTests(TestCase):
    """Test product list view."""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        
        # Create test products
        self.product1 = Product.objects.create(
            sku='TEST-001',
            name='Product 1',
            description='Description 1',
            category=self.category,
            price=99.99,
            cost=49.99,
            quantity=100,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.product2 = Product.objects.create(
            sku='TEST-002',
            name='Product 2',
            description='Description 2',
            category=self.category,
            price=199.99,
            cost=99.99,
            quantity=50,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.list_url = reverse('products:list')
    
    def test_product_list_requires_login(self):
        """Test product list requires authentication."""
        response = self.client.get(self.list_url)
        self.assertRedirects(response, f"{reverse('users:login')}?next={self.list_url}")
    
    def test_product_list_view(self):
        """Test product list view."""
        self.client.force_login(self.user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/list.html')
        self.assertContains(response, 'Product 1')
        self.assertContains(response, 'Product 2')
        self.assertEqual(len(response.context['products']), 2)
    
    def test_product_list_search(self):
        """Test product list with search."""
        self.client.force_login(self.user)
        response = self.client.get(self.list_url, {'search': 'Product 1'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Product 1')
        self.assertNotContains(response, 'Product 2')
    
    def test_product_list_filter_by_category(self):
        """Test product list filtered by category."""
        self.client.force_login(self.user)
        
        # Create another category
        other_category = Category.objects.create(name='Books')
        
        response = self.client.get(self.list_url, {'category': self.category.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 2)
        
        response = self.client.get(self.list_url, {'category': other_category.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['products']), 0)


class ProductDetailViewTests(TestCase):
    """Test product detail view."""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        
        self.product = Product.objects.create(
            sku='TEST-001',
            name='Test Product',
            description='Test description',
            category=self.category,
            price=99.99,
            cost=49.99,
            quantity=100,
            created_by=self.user,
            updated_by=self.user,
        )
        
        self.detail_url = reverse('products:detail', kwargs={'pk': self.product.pk})
    
    def test_product_detail_requires_login(self):
        """Test product detail requires authentication."""
        response = self.client.get(self.detail_url)
        self.assertRedirects(response, f"{reverse('users:login')}?next={self.detail_url}")
    
    def test_product_detail_view(self):
        """Test product detail view."""
        self.client.force_login(self.user)
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/detail.html')
        self.assertContains(response, 'Test Product')
        self.assertContains(response, 'TEST-001')
        self.assertEqual(response.context['product'], self.product)


class ProductCreateViewTests(TestCase):
    """Test product create view."""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        
        # Create staff user
        self.staff_user = self.User.objects.create_user(
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = self.User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        self.create_url = reverse('products:create')
    
    def test_product_create_requires_login(self):
        """Test product create requires authentication."""
        response = self.client.get(self.create_url)
        self.assertRedirects(response, f"{reverse('users:login')}?next={self.create_url}")
    
    def test_product_create_requires_staff(self):
        """Test product create requires staff permission."""
        self.client.force_login(self.regular_user)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_product_create_view_get(self):
        """Test GET request to product create page."""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.create_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/form.html')
        self.assertContains(response, 'Create Product')
    
    def test_product_create_view_post(self):
        """Test POST request to create product."""
        self.client.force_login(self.staff_user)
        
        data = {
            'sku': 'NEW-001',
            'name': 'New Product',
            'description': 'New product description',
            'category': self.category.id,
            'price': 149.99,
            'cost': 79.99,
            'quantity': 50,
            'min_quantity': 5,
            'max_quantity': 500,
            'status': 'active',
        }
        
        response = self.client.post(self.create_url, data)
        
        # Should redirect to product list
        self.assertRedirects(response, reverse('products:list'))
        
        # Check product was created
        product = Product.objects.get(sku='NEW-001')
        self.assertEqual(product.name, 'New Product')
        self.assertEqual(product.created_by, self.staff_user)
