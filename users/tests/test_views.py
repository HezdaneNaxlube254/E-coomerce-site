"""
Tests for users views.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from faker import Faker

fake = Faker()


class LoginViewTests(TestCase):
    """Test login view."""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.login_url = reverse('users:login')
    
    def test_login_get(self):
        """Test GET request to login page."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertContains(response, 'Login')
    
    def test_login_post_success(self):
        """Test successful login."""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('products:list'))
        self.assertTrue('_auth_user_id' in self.client.session)
    
    def test_login_post_invalid(self):
        """Test login with invalid credentials."""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')
        self.assertFalse('_auth_user_id' in self.client.session)
    
    def test_login_redirect_authenticated(self):
        """Test authenticated user is redirected from login page."""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('products:list'))


class LogoutViewTests(TestCase):
    """Test logout view."""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.logout_url = reverse('users:logout')
    
    def test_logout(self):
        """Test logout functionality."""
        self.client.force_login(self.user)
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('users:login'))
        self.assertFalse('_auth_user_id' in self.client.session)


class ProfileViewTests(TestCase):
    """Test profile view."""
    
    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe',
        )
        self.profile_url = reverse('users:profile')
    
    def test_profile_view_requires_login(self):
        """Test profile view requires authentication."""
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f"{reverse('users:login')}?next={self.profile_url}")
    
    def test_profile_view_get(self):
        """Test GET request to profile page."""
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertContains(response, 'John')
    
    def test_profile_update(self):
        """Test updating profile."""
        self.client.force_login(self.user)
        response = self.client.post(self.profile_url, {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone': '1234567890',
            'department': 'Engineering',
            'position': 'Developer',
        })
        self.assertRedirects(response, self.profile_url)
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Smith')
        self.assertEqual(self.user.phone, '1234567890')
