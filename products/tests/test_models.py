"""
Tests for products models.
"""

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from faker import Faker

from products.models import Category, Product, ProductAuditLog

fake = Faker()


class CategoryModelTests(TestCase):
    """Test Category model."""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices and accessories'
        )
    
    def test_create_category(self):
        """Test creating a category."""
        self.assertEqual(self.category.name, 'Electronics')
        self.assertEqual(str(self.category), 'Electronics')
    
    def test_category_ordering(self):
        """Test categories are ordered by name."""
        Category.objects.create(name='Books')
        Category.objects.create(name='Clothing')
        
        categories = Category.objects.all()
        self.assertEqual(categories[0].name, 'Books')
        self.assertEqual(categories[1].name, 'Clothing')
        self.assertEqual(categories[2].name, 'Electronics')


class ProductModelTests(TestCase):
    """Test Product model."""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='test123'
        )
        
        self.category = Category.objects.create(name='Electronics')
        
        self.product_data = {
            'sku': 'TEST-001',
            'name': 'Test Product',
            'description': 'Test product description',
            'category': self.category,
            'price': 99.99,
            'cost': 49.99,
            'quantity': 100,
            'min_quantity': 10,
            'max_quantity': 1000,
            'status': 'active',
            'created_by': self.user,
            'updated_by': self.user,
        }
    
    def test_create_product(self):
        """Test creating a product."""
        product = Product.objects.create(**self.product_data)
        
        self.assertEqual(product.sku, 'TEST-001')
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.price, 99.99)
        self.assertEqual(product.cost, 49.99)
        self.assertEqual(product.quantity, 100)
        self.assertTrue(product.is_available)
        self.assertFalse(product.needs_restock)
    
    def test_product_clean_valid(self):
        """Test product clean method with valid data."""
        product = Product(**self.product_data)
        product.full_clean()  # Should not raise
    
    def test_product_clean_price_less_than_cost(self):
        """Test product clean with price less than cost."""
        product = Product(**self.product_data)
        product.price = 40.00  # Less than cost
        product.cost = 49.99
        
        with self.assertRaises(ValidationError):
            product.full_clean()
    
    def test_product_clean_negative_quantity(self):
        """Test product clean with negative quantity."""
        product = Product(**self.product_data)
        product.quantity = -10
        
        with self.assertRaises(ValidationError):
            product.full_clean()
    
    def test_product_clean_max_less_than_min(self):
        """Test product clean with max quantity less than min."""
        product = Product(**self.product_data)
        product.max_quantity = 5
        product.min_quantity = 10
        
        with self.assertRaises(ValidationError):
            product.full_clean()
    
    def test_product_margin(self):
        """Test profit margin calculation."""
        product = Product.objects.create(**self.product_data)
        expected_margin = ((99.99 - 49.99) / 99.99) * 100
        self.assertAlmostEqual(product.margin, expected_margin, places=2)
    
    def test_needs_restock(self):
        """Test needs_restock property."""
        product = Product.objects.create(**self.product_data)
        
        # Above min quantity
        product.quantity = 100
        self.assertFalse(product.needs_restock)
        
        # At min quantity
        product.quantity = 10
        self.assertFalse(product.needs_restock)
        
        # Below min quantity
        product.quantity = 5
        self.assertTrue(product.needs_restock)
    
    def test_is_available(self):
        """Test is_available property."""
        product = Product.objects.create(**self.product_data)
        
        # Active with stock
        product.status = 'active'
        product.quantity = 10
        self.assertTrue(product.is_available)
        
        # Inactive
        product.status = 'inactive'
        self.assertFalse(product.is_available)
        
        # Out of stock
        product.status = 'active'
        product.quantity = 0
        self.assertFalse(product.is_available)
    
    def test_decrement_quantity(self):
        """Test decrement_quantity method."""
        product = Product.objects.create(**self.product_data)
        product.quantity = 50
        
        # Valid decrement
        product.decrement_quantity(10)
        product.refresh_from_db()
        self.assertEqual(product.quantity, 40)
        
        # Invalid decrement (insufficient stock)
        with self.assertRaises(ValidationError):
            product.decrement_quantity(100)
    
    def test_decrement_quantity_to_zero(self):
        """Test decrementing to zero changes status."""
        product = Product.objects.create(**self.product_data)
        product.quantity = 5
        
        product.decrement_quantity(5)
        product.refresh_from_db()
        
        self.assertEqual(product.quantity, 0)
        self.assertEqual(product.status, 'out_of_stock')


class ProductAuditLogModelTests(TestCase):
    """Test ProductAuditLog model."""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='test123'
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
    
    def test_create_audit_log(self):
        """Test creating audit log."""
        audit_log = ProductAuditLog.objects.create(
            product=self.product,
            user=self.user,
            action='create',
            changes={'field': 'value'},
            notes='Test notes',
        )
        
        self.assertEqual(audit_log.product, self.product)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'create')
        self.assertEqual(audit_log.changes, {'field': 'value'})
        self.assertEqual(audit_log.notes, 'Test notes')
        self.assertEqual(str(audit_log), f"{self.product.sku} - create - {audit_log.timestamp}")
