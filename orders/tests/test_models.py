"""
Tests for orders models.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from faker import Faker

from orders.models import Order, OrderItem
from products.models import Product, Category

fake = Faker()


class OrderModelTests(TestCase):
    """Test Order model."""
    
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
    
    def test_create_order(self):
        """Test creating an order."""
        order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_phone='1234567890',
            customer_address='123 Main St',
            created_by=self.user,
        )
        
        self.assertTrue(order.order_number.startswith('ORD-'))
        self.assertEqual(order.status, 'draft')
        self.assertEqual(order.customer_name, 'John Doe')
        self.assertEqual(order.created_by, self.user)
        self.assertTrue(order.can_be_modified)
        self.assertTrue(order.can_be_cancelled)
        self.assertFalse(order.is_completed)
    
    def test_order_number_generation(self):
        """Test automatic order number generation."""
        order1 = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
        )
        
        order2 = Order.objects.create(
            customer_name='Jane Smith',
            customer_email='jane@example.com',
            customer_address='456 Oak St',
            created_by=self.user,
        )
        
        self.assertNotEqual(order1.order_number, order2.order_number)
        self.assertTrue(order1.order_number.startswith('ORD-'))
        self.assertTrue(order2.order_number.startswith('ORD-'))
    
    def test_order_status_transitions_valid(self):
        """Test valid order status transitions."""
        order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
        )
        
        # Draft -> Pending
        order.status = 'pending'
        order.full_clean()  # Should not raise
        order.save()
        
        # Pending -> Processing
        order.status = 'processing'
        order.full_clean()
        order.save()
        
        # Processing -> Shipped
        order.status = 'shipped'
        order.full_clean()
        order.save()
        
        # Shipped -> Delivered
        order.status = 'delivered'
        order.full_clean()
        order.save()
    
    def test_order_status_transitions_invalid(self):
        """Test invalid order status transitions."""
        order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
            status='shipped'
        )
        
        # Shipped -> Processing (invalid)
        order.status = 'processing'
        with self.assertRaises(ValidationError):
            order.full_clean()
        
        # Delivered -> Shipped (invalid)
        order.status = 'delivered'
        order.save()  # Save first to get delivered status
        
        order.status = 'shipped'
        with self.assertRaises(ValidationError):
            order.full_clean()
    
    def test_order_totals(self):
        """Test order total calculation."""
        order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
        )
        
        # Add items
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )
        
        order.refresh_from_db()
        expected_total = 2 * self.product.price
        self.assertEqual(order.total_amount, expected_total)
        self.assertEqual(order.final_amount, expected_total)  # No tax/discount
    
    def test_cancel_order(self):
        """Test cancelling an order."""
        order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
            status='pending'
        )
        
        # Add item
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=10,
            unit_price=self.product.price
        )
        
        initial_stock = self.product.quantity
        
        order.cancel_order(self.user, 'Customer requested')
        
        self.assertEqual(order.status, 'cancelled')
        self.assertTrue(order.is_completed)
        
        # Check stock was restored
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, initial_stock)
    
    def test_process_order(self):
        """Test processing an order."""
        order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
            status='pending'
        )
        
        # Add item
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=5,
            unit_price=self.product.price
        )
        
        initial_stock = self.product.quantity
        
        order.process_order(self.user)
        
        self.assertEqual(order.status, 'processing')
        self.assertEqual(order.assigned_to, self.user)
        
        # Check stock was deducted
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, initial_stock - 5)
    
    def test_process_order_insufficient_stock(self):
        """Test processing order with insufficient stock."""
        order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
            status='pending'
        )
        
        # Add item with quantity greater than stock
        item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=200,  # More than available stock (100)
            unit_price=self.product.price
        )
        
        with self.assertRaises(ValidationError):
            order.process_order(self.user)


class OrderItemModelTests(TestCase):
    """Test OrderItem model."""
    
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
        
        self.order = Order.objects.create(
            customer_name='John Doe',
            customer_email='john@example.com',
            customer_address='123 Main St',
            created_by=self.user,
        )
    
    def test_create_order_item(self):
        """Test creating an order item."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            unit_price=self.product.price
        )
        
        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.unit_price, self.product.price)
        self.assertEqual(item.total_price, 3 * self.product.price)
        self.assertEqual(str(item), f"{self.product.name} x3")
    
    def test_order_item_save_updates_order_totals(self):
        """Test that saving order item updates order totals."""
        initial_total = self.order.total_amount
        
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )
        
        self.order.refresh_from_db()
        expected_total = 2 * self.product.price
        self.assertEqual(self.order.total_amount, expected_total)
    
    def test_order_item_delete_updates_order_totals(self):
        """Test that deleting order item updates order totals."""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            unit_price=self.product.price
        )
        
        item.delete()
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, 0)
