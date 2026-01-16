"""
Tests for users models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from faker import Faker

from users.models import AuditLog

fake = Faker()


class UserModelTests(TestCase):
    """Test User model."""
    
    def setUp(self):
        self.User = get_user_model()
        self.user_data = {
            'email': fake.email(),
            'password': 'testpass123',
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'phone': fake.phone_number()[:20],
            'department': fake.job(),
            'position': fake.job(),
        }
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = self.User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_create_user_no_email(self):
        """Test creating user without email raises error."""
        with self.assertRaises(ValueError):
            self.User.objects.create_user(email='', password='test123')
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = self.User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_user_str(self):
        """Test user string representation."""
        user = self.User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])
    
    def test_user_roles(self):
        """Test user role properties."""
        # Regular user (viewer)
        user = self.User.objects.create_user(**self.user_data)
        self.assertTrue(user.is_viewer)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff_member)
        
        # Staff member
        staff_user = self.User.objects.create_user(
            email='staff@example.com',
            password='test123',
            is_staff=True
        )
        self.assertFalse(staff_user.is_viewer)
        self.assertFalse(staff_user.is_admin)
        self.assertTrue(staff_user.is_staff_member)
        
        # Admin
        admin_user = self.User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertFalse(admin_user.is_viewer)
        self.assertTrue(admin_user.is_admin)
        self.assertFalse(admin_user.is_staff_member)


class AuditLogModelTests(TestCase):
    """Test AuditLog model."""
    
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='test123'
        )
    
    def test_create_audit_log(self):
        """Test creating audit log."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='login',
            model_name='User',
            object_id=str(self.user.id),
            details={'ip': '127.0.0.1'},
            ip_address='127.0.0.1',
            user_agent='Test Agent',
        )
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'login')
        self.assertEqual(audit_log.model_name, 'User')
        self.assertEqual(str(audit_log), f"{self.user} - login - User - {audit_log.timestamp}")
    
    def test_audit_log_ordering(self):
        """Test audit logs are ordered by timestamp descending."""
        AuditLog.objects.create(
            user=self.user,
            action='login',
            model_name='User',
            object_id=str(self.user.id),
        )
        AuditLog.objects.create(
            user=self.user,
            action='logout',
            model_name='User',
            object_id=str(self.user.id),
        )
        
        logs = AuditLog.objects.all()
        self.assertEqual(logs[0].action, 'logout')
        self.assertEqual(logs[1].action, 'login')
