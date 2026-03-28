from datetime import date
from decimal import Decimal

from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from app.models import Client, Invoice, InvoiceItem, User, UserCompany


class ViewTestMixin:
    """Set up shared test data for all view tests."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='test@example.com', password='testpass123'
        )
        cls.client_obj = Client.objects.create(
            user=cls.user,
            name='Acme Corp',
            client_type=Client.CLIENT_BUSINESS,
            email='acme@example.com',
            city='Vilnius',
        )
        cls.invoice = Invoice.objects.create(
            user=cls.user,
            client=cls.client_obj,
            series='VF',
            number=1,
            status=Invoice.STATUS_DRAFT,
            issue_date=date(2025, 1, 15),
            due_date=date(2025, 2, 15),
        )
        InvoiceItem.objects.create(
            invoice=cls.invoice,
            description='Web development',
            quantity=Decimal('10.00'),
            unit_price=Decimal('100.00'),
        )
        cls.company = UserCompany.objects.create(
            user=cls.user,
            company_name='My Company',
            company_code='123456',
        )

    def setUp(self):
        self.client.force_login(self.user)


class DashboardViewTests(ViewTestMixin, TestCase):

    def test_dashboard_full_page(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_dashboard_htmx_returns_partial(self):
        response = self.client.get(
            reverse('dashboard'), HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/dashboard_partial.html')


class InvoiceListViewTests(ViewTestMixin, TestCase):

    def test_invoice_list_full_page(self):
        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/invoice_list.html')
        self.assertContains(response, 'VF-000001')

    def test_invoice_list_htmx_returns_partial(self):
        response = self.client.get(
            reverse('invoice_list'), HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/invoice_list_partial.html')
        self.assertNotContains(response, '<!DOCTYPE html>')

    def test_invoice_list_status_filter(self):
        response = self.client.get(
            reverse('invoice_list'), {'status': 'draft'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VF-000001')

    def test_invoice_list_status_filter_no_match(self):
        response = self.client.get(
            reverse('invoice_list'), {'status': 'paid'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No invoices')

    def test_invoice_list_pagination(self):
        # Create enough invoices to require pagination
        for i in range(2, 15):
            Invoice.objects.create(
                user=self.user,
                client=self.client_obj,
                series='VF',
                number=i,
                status=Invoice.STATUS_DRAFT,
                issue_date=date(2025, 1, 15),
                due_date=date(2025, 2, 15),
            )
        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_next())

        response_p2 = self.client.get(reverse('invoice_list'), {'page': 2})
        self.assertEqual(response_p2.status_code, 200)

    def test_invoice_list_empty(self):
        Invoice.objects.all().delete()
        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No invoices')


class ClientListViewTests(ViewTestMixin, TestCase):

    def test_client_list_full_page(self):
        response = self.client.get(reverse('client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/client_list.html')
        self.assertContains(response, 'Acme Corp')

    def test_client_list_htmx_returns_partial(self):
        response = self.client.get(
            reverse('client_list'), HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/client_list_partial.html')
        self.assertNotContains(response, '<!DOCTYPE html>')

    def test_client_list_type_filter(self):
        response = self.client.get(
            reverse('client_list'), {'client_type': 'business'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Corp')

    def test_client_list_type_filter_no_match(self):
        response = self.client.get(
            reverse('client_list'), {'client_type': 'individual'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No clients')

    def test_client_list_empty(self):
        Invoice.objects.all().delete()
        Client.objects.all().delete()
        response = self.client.get(reverse('client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No clients')


class CompanyListViewTests(ViewTestMixin, TestCase):

    def test_company_list_full_page(self):
        response = self.client.get(reverse('company_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/company_list.html')
        self.assertContains(response, 'My Company')

    def test_company_list_htmx_returns_partial(self):
        response = self.client.get(
            reverse('company_list'), HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/company_list_partial.html')
        self.assertNotContains(response, '<!DOCTYPE html>')

    def test_company_list_empty(self):
        UserCompany.objects.all().delete()
        response = self.client.get(reverse('company_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No companies')


class PaginationComponentTests(ViewTestMixin, TestCase):

    def test_pagination_not_shown_single_page(self):
        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'aria-label="Pagination"')

    def test_pagination_shown_multiple_pages(self):
        for i in range(2, 15):
            Invoice.objects.create(
                user=self.user,
                client=self.client_obj,
                series='VF',
                number=i,
                status=Invoice.STATUS_DRAFT,
                issue_date=date(2025, 1, 15),
                due_date=date(2025, 2, 15),
            )
        response = self.client.get(reverse('invoice_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-label="Pagination"')
        self.assertContains(response, 'hx-get')


class HtmxNavigationTests(ViewTestMixin, TestCase):

    def test_sidebar_has_htmx_attributes(self):
        response = self.client.get(reverse('dashboard'))
        content = response.content.decode()
        self.assertIn('hx-get', content)
        self.assertIn('hx-target="#main-content"', content)
        self.assertIn('hx-swap="innerHTML"', content)
        self.assertIn('hx-push-url="true"', content)


from django.contrib.auth import get_user_model
from django.test import Client as DjangoTestClient, TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = DjangoTestClient()
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
        self.client = DjangoTestClient()

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
        self.client = DjangoTestClient()
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
        self.client = DjangoTestClient()

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
        self.client = DjangoTestClient()

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")


class InvoiceSearchTests(ViewTestMixin, TestCase):

    def test_search_by_client_name(self):
        response = self.client.get(reverse('invoice_list'), {'search': 'Acme'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VF-000001')

    def test_search_no_match(self):
        response = self.client.get(reverse('invoice_list'), {'search': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No invoices')

    def test_search_by_series(self):
        response = self.client.get(reverse('invoice_list'), {'search': 'VF'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VF-000001')

    def test_search_combined_with_status_filter(self):
        response = self.client.get(
            reverse('invoice_list'), {'search': 'Acme', 'status': 'draft'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VF-000001')

    def test_search_combined_with_status_filter_no_match(self):
        response = self.client.get(
            reverse('invoice_list'), {'search': 'Acme', 'status': 'paid'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No invoices')

    def test_search_htmx_returns_partial(self):
        response = self.client.get(
            reverse('invoice_list'), {'search': 'Acme'}, HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/invoice_list_partial.html')

    def test_search_context_has_current_search(self):
        response = self.client.get(reverse('invoice_list'), {'search': 'Acme'})
        self.assertEqual(response.context['current_search'], 'Acme')

    def test_empty_search_returns_all(self):
        response = self.client.get(reverse('invoice_list'), {'search': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VF-000001')


class ClientSearchTests(ViewTestMixin, TestCase):

    def test_search_by_name(self):
        response = self.client.get(reverse('client_list'), {'search': 'Acme'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Corp')

    def test_search_by_email(self):
        response = self.client.get(reverse('client_list'), {'search': 'acme@example'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Corp')

    def test_search_by_city(self):
        response = self.client.get(reverse('client_list'), {'search': 'Vilnius'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Corp')

    def test_search_no_match(self):
        response = self.client.get(reverse('client_list'), {'search': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No clients')

    def test_search_combined_with_type_filter(self):
        response = self.client.get(
            reverse('client_list'), {'search': 'Acme', 'client_type': 'business'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Corp')

    def test_search_combined_with_type_filter_no_match(self):
        response = self.client.get(
            reverse('client_list'), {'search': 'Acme', 'client_type': 'individual'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No clients')

    def test_search_htmx_returns_partial(self):
        response = self.client.get(
            reverse('client_list'), {'search': 'Acme'}, HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lists/client_list_partial.html')

    def test_search_context_has_current_search(self):
        response = self.client.get(reverse('client_list'), {'search': 'Acme'})
        self.assertEqual(response.context['current_search'], 'Acme')

    def test_empty_search_returns_all(self):
        response = self.client.get(reverse('client_list'), {'search': ''})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme Corp')
