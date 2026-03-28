from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123'
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'test@example.com', 'password': 'testpass123'},
        )
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            reverse('login'),
            {'username': 'test@example.com', 'password': 'wrongpass'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct email and password')

    def test_authenticated_user_redirected_from_login(self):
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('dashboard'))


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page_renders(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create account')

    def test_register_with_valid_data(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'new@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password1': 'securepass123!',
                'password2': 'securepass123!',
            },
        )
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_register_with_mismatched_passwords(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'new@example.com',
                'password1': 'securepass123!',
                'password2': 'differentpass123!',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new@example.com').exists())

    def test_register_with_duplicate_email(self):
        User.objects.create_user(email='existing@example.com', password='testpass123')
        response = self.client.post(
            reverse('register'),
            {
                'email': 'existing@example.com',
                'password1': 'securepass123!',
                'password2': 'securepass123!',
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_redirected_from_register(self):
        user = User.objects.create_user(
            email='test@example.com', password='testpass123'
        )
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('register'))
        self.assertRedirects(response, reverse('dashboard'))


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com', password='testpass123'
        )

    def test_logout_redirects_to_login(self):
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_password_reset_page_renders(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Send reset link')

    def test_password_reset_done_page_renders(self):
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Check your email')

    def test_password_reset_complete_page_renders(self):
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password reset complete')


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class DashboardAccessTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")
