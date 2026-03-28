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
from django.test import Client as DjangoTestClient
from django.test import TestCase as DjangoTestCase
from django.test import override_settings
from django.urls import reverse as url_reverse

AuthUser = get_user_model()


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class LoginViewTests(DjangoTestCase):
    def setUp(self):
        self.client = DjangoTestClient()
        self.user = AuthUser.objects.create_user(
            email='test@example.com', password='testpass123'
        )

    def test_login_page_renders(self):
        response = self.client.get(url_reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            url_reverse('login'),
            {'username': 'test@example.com', 'password': 'testpass123'},
        )
        self.assertRedirects(response, url_reverse('dashboard'))

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            url_reverse('login'),
            {'username': 'test@example.com', 'password': 'wrongpass'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct email and password')

    def test_authenticated_user_redirected_from_login(self):
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(url_reverse('login'))
        self.assertRedirects(response, url_reverse('dashboard'))


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class RegisterViewTests(DjangoTestCase):
    def setUp(self):
        self.client = DjangoTestClient()

    def test_register_page_renders(self):
        response = self.client.get(url_reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create account')

    def test_register_with_valid_data(self):
        response = self.client.post(
            url_reverse('register'),
            {
                'email': 'new@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password1': 'securepass123!',
                'password2': 'securepass123!',
            },
        )
        self.assertRedirects(response, url_reverse('dashboard'))
        self.assertTrue(AuthUser.objects.filter(email='new@example.com').exists())

    def test_register_with_mismatched_passwords(self):
        response = self.client.post(
            url_reverse('register'),
            {
                'email': 'new@example.com',
                'password1': 'securepass123!',
                'password2': 'differentpass123!',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AuthUser.objects.filter(email='new@example.com').exists())

    def test_register_with_duplicate_email(self):
        AuthUser.objects.create_user(email='existing@example.com', password='testpass123')
        response = self.client.post(
            url_reverse('register'),
            {
                'email': 'existing@example.com',
                'password1': 'securepass123!',
                'password2': 'securepass123!',
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_redirected_from_register(self):
        user = AuthUser.objects.create_user(
            email='test@example.com', password='testpass123'
        )
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(url_reverse('register'))
        self.assertRedirects(response, url_reverse('dashboard'))


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class LogoutViewTests(DjangoTestCase):
    def setUp(self):
        self.client = DjangoTestClient()
        self.user = AuthUser.objects.create_user(
            email='test@example.com', password='testpass123'
        )

    def test_logout_redirects_to_login(self):
        self.client.login(username='test@example.com', password='testpass123')
        response = self.client.get(url_reverse('logout'))
        self.assertRedirects(response, url_reverse('login'))


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class PasswordResetViewTests(DjangoTestCase):
    def setUp(self):
        self.client = DjangoTestClient()

    def test_password_reset_page_renders(self):
        response = self.client.get(url_reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Send reset link')

    def test_password_reset_done_page_renders(self):
        response = self.client.get(url_reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Check your email')

    def test_password_reset_complete_page_renders(self):
        response = self.client.get(url_reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password reset complete')


@override_settings(
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class DashboardAccessTests(DjangoTestCase):
    def setUp(self):
        self.client = DjangoTestClient()

    def test_dashboard_requires_login(self):
        response = self.client.get(url_reverse('dashboard'))
        self.assertRedirects(response, f"{url_reverse('login')}?next={url_reverse('dashboard')}")


# ---------------------------------------------------------------------------
# CRUD Tests
# ---------------------------------------------------------------------------

class ClientCrudTests(ViewTestMixin, TestCase):

    def test_client_create_get(self):
        response = self.client.get(reverse('client_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/client_form.html')

    def test_client_create_post(self):
        response = self.client.post(reverse('client_create'), {
            'client_type': 'individual',
            'name': 'New Client',
        })
        self.assertRedirects(response, reverse('client_list'))
        self.assertTrue(Client.objects.filter(name='New Client').exists())

    def test_client_edit_get(self):
        response = self.client.get(reverse('client_edit', args=[self.client_obj.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/client_form.html')

    def test_client_edit_post(self):
        response = self.client.post(
            reverse('client_edit', args=[self.client_obj.pk]),
            {
                'client_type': 'business',
                'name': 'Updated Corp',
            },
        )
        self.assertRedirects(response, reverse('client_list'))
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.name, 'Updated Corp')

    def test_client_delete_get(self):
        Invoice.objects.all().delete()
        response = self.client.get(reverse('client_delete', args=[self.client_obj.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/confirm_delete.html')

    def test_client_delete_post(self):
        Invoice.objects.all().delete()
        response = self.client.post(reverse('client_delete', args=[self.client_obj.pk]))
        self.assertRedirects(response, reverse('client_list'))
        self.assertFalse(Client.objects.filter(pk=self.client_obj.pk).exists())

    def test_client_crud_requires_login(self):
        self.client.logout()
        for url_name in ('client_create',):
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 302)


class CompanyCrudTests(ViewTestMixin, TestCase):

    def test_company_create_get(self):
        response = self.client.get(reverse('company_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/company_form.html')

    def test_company_create_post(self):
        UserCompany.objects.all().delete()
        response = self.client.post(reverse('company_create'), {
            'company_name': 'New Co',
            'company_code': '999999',
        })
        self.assertRedirects(response, reverse('company_list'))
        self.assertTrue(UserCompany.objects.filter(company_name='New Co').exists())

    def test_company_edit_get(self):
        response = self.client.get(reverse('company_edit', args=[self.company.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/company_form.html')

    def test_company_edit_post(self):
        response = self.client.post(
            reverse('company_edit', args=[self.company.pk]),
            {
                'company_name': 'Updated Co',
                'company_code': '654321',
            },
        )
        self.assertRedirects(response, reverse('company_list'))
        self.company.refresh_from_db()
        self.assertEqual(self.company.company_name, 'Updated Co')

    def test_company_delete_post(self):
        response = self.client.post(reverse('company_delete', args=[self.company.pk]))
        self.assertRedirects(response, reverse('company_list'))
        self.assertFalse(UserCompany.objects.filter(pk=self.company.pk).exists())


class InvoiceCrudTests(ViewTestMixin, TestCase):

    def test_invoice_create_get(self):
        response = self.client.get(reverse('invoice_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/invoice_form.html')

    def test_invoice_create_post(self):
        response = self.client.post(reverse('invoice_create'), {
            'client': self.client_obj.pk,
            'series': 'VF',
            'number': 99,
            'status': 'draft',
            'issue_date': '2025-03-01',
            'due_date': '2025-04-01',
            'tax_enabled': True,
            'tax_rate': '21.00',
            'notes': '',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-description': 'Test item',
            'items-0-unit': 'hr',
            'items-0-quantity': '5',
            'items-0-unit_price': '50.00',
        })
        self.assertRedirects(response, reverse('invoice_list'))
        self.assertTrue(Invoice.objects.filter(number=99).exists())

    def test_invoice_edit_get(self):
        response = self.client.get(reverse('invoice_edit', args=[self.invoice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/invoice_form.html')

    def test_invoice_edit_post(self):
        item = self.invoice.items.first()
        response = self.client.post(
            reverse('invoice_edit', args=[self.invoice.pk]),
            {
                'client': self.client_obj.pk,
                'series': 'VF',
                'number': 1,
                'status': 'sent',
                'issue_date': '2025-01-15',
                'due_date': '2025-02-15',
                'tax_enabled': True,
                'tax_rate': '21.00',
                'notes': 'Updated',
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '1',
                'items-MIN_NUM_FORMS': '0',
                'items-MAX_NUM_FORMS': '1000',
                'items-0-id': item.pk,
                'items-0-description': 'Web development',
                'items-0-unit': '',
                'items-0-quantity': '10.00',
                'items-0-unit_price': '100.00',
            },
        )
        self.assertRedirects(response, reverse('invoice_list'))
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'sent')

    def test_invoice_delete_post(self):
        response = self.client.post(reverse('invoice_delete', args=[self.invoice.pk]))
        self.assertRedirects(response, reverse('invoice_list'))
        self.assertFalse(Invoice.objects.filter(pk=self.invoice.pk).exists())

    def test_invoice_line_item_add(self):
        """Creating an invoice with multiple line items works."""
        response = self.client.post(reverse('invoice_create'), {
            'client': self.client_obj.pk,
            'series': 'VF',
            'number': 50,
            'status': 'draft',
            'issue_date': '2025-03-01',
            'due_date': '2025-04-01',
            'tax_enabled': True,
            'tax_rate': '21.00',
            'notes': '',
            'items-TOTAL_FORMS': '2',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-description': 'Item 1',
            'items-0-unit': 'hr',
            'items-0-quantity': '1',
            'items-0-unit_price': '10.00',
            'items-1-description': 'Item 2',
            'items-1-unit': 'hr',
            'items-1-quantity': '2',
            'items-1-unit_price': '20.00',
        })
        self.assertRedirects(response, reverse('invoice_list'))
        inv = Invoice.objects.get(number=50)
        self.assertEqual(inv.items.count(), 2)

    def test_invoice_line_item_remove(self):
        """Deleting a line item via formset DELETE flag works."""
        item = self.invoice.items.first()
        response = self.client.post(
            reverse('invoice_edit', args=[self.invoice.pk]),
            {
                'client': self.client_obj.pk,
                'series': 'VF',
                'number': 1,
                'status': 'draft',
                'issue_date': '2025-01-15',
                'due_date': '2025-02-15',
                'tax_enabled': True,
                'tax_rate': '21.00',
                'notes': '',
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '1',
                'items-MIN_NUM_FORMS': '0',
                'items-MAX_NUM_FORMS': '1000',
                'items-0-id': item.pk,
                'items-0-description': 'Web development',
                'items-0-unit': '',
                'items-0-quantity': '10.00',
                'items-0-unit_price': '100.00',
                'items-0-DELETE': 'on',
            },
        )
        self.assertRedirects(response, reverse('invoice_list'))
        self.assertEqual(self.invoice.items.count(), 0)


class ProfileCrudTests(ViewTestMixin, TestCase):

    def test_profile_edit_get(self):
        response = self.client.get(reverse('profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'crud/profile_form.html')

    def test_profile_edit_post(self):
        response = self.client.post(reverse('profile_edit'), {
            'phone_number': '+37060000000',
            'address': '123 Main St',
            'city': 'Vilnius',
            'personal_code': '12345678901',
            'postal_code': 'LT-01001',
            'apartment_number': '5',
            'bank_account': 'LT123456789012345678',
            'bank_name': 'Swedbank',
        })
        self.assertRedirects(response, reverse('profile_edit'))
        from app.models import UserProfile
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.city, 'Vilnius')
        self.assertEqual(profile.bank_name, 'Swedbank')


class HtmxDeleteTests(ViewTestMixin, TestCase):
    """Test that HTMX delete requests return empty body with HX-Trigger header."""

    def test_invoice_htmx_delete_returns_empty_response(self):
        response = self.client.post(
            reverse('invoice_delete', args=[self.invoice.pk]),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertIn('showMessage', response['HX-Trigger'])
        self.assertFalse(Invoice.objects.filter(pk=self.invoice.pk).exists())

    def test_client_htmx_delete_returns_empty_response(self):
        Invoice.objects.all().delete()
        response = self.client.post(
            reverse('client_delete', args=[self.client_obj.pk]),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertIn('showMessage', response['HX-Trigger'])
        self.assertFalse(Client.objects.filter(pk=self.client_obj.pk).exists())

    def test_company_htmx_delete_returns_empty_response(self):
        response = self.client.post(
            reverse('company_delete', args=[self.company.pk]),
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'')
        self.assertIn('showMessage', response['HX-Trigger'])
        self.assertFalse(UserCompany.objects.filter(pk=self.company.pk).exists())


class SwapTargetTests(ViewTestMixin, TestCase):
    """Test that filter buttons target #main-content instead of #list-container."""

    def test_invoice_filter_targets_main_content(self):
        response = self.client.get(
            reverse('invoice_list'), HTTP_HX_REQUEST='true'
        )
        content = response.content.decode()
        self.assertNotIn('hx-target="#list-container"', content)
        self.assertIn('hx-target="#main-content"', content)

    def test_client_filter_targets_main_content(self):
        response = self.client.get(
            reverse('client_list'), HTTP_HX_REQUEST='true'
        )
        content = response.content.decode()
        self.assertNotIn('hx-target="#list-container"', content)
        self.assertIn('hx-target="#main-content"', content)

    def test_invoice_list_has_hx_confirm_delete(self):
        response = self.client.get(
            reverse('invoice_list'), HTTP_HX_REQUEST='true'
        )
        content = response.content.decode()
        self.assertIn('hx-confirm=', content)
        self.assertIn('hx-post=', content)


class FormCenteringTests(ViewTestMixin, TestCase):
    """Form containers are horizontally centered with mx-auto."""

    def test_client_form_centered(self):
        response = self.client.get(reverse('client_create'))
        self.assertContains(response, 'max-w-2xl mx-auto')

    def test_company_form_centered(self):
        response = self.client.get(reverse('company_create'))
        self.assertContains(response, 'max-w-2xl mx-auto')

    def test_profile_form_centered(self):
        response = self.client.get(reverse('profile_edit'))
        self.assertContains(response, 'max-w-2xl mx-auto')

    def test_invoice_form_centered(self):
        response = self.client.get(reverse('invoice_create'))
        self.assertContains(response, 'max-w-4xl mx-auto')

    def test_confirm_delete_centered(self):
        response = self.client.get(
            reverse('client_delete', args=[self.client_obj.pk])
        )
        self.assertContains(response, 'max-w-lg mx-auto')


class Select2WidgetTests(ViewTestMixin, TestCase):
    """Select fields use django-select2 widgets."""

    def test_invoice_form_client_uses_select2(self):
        response = self.client.get(reverse('invoice_create'))
        self.assertContains(response, 'django-select2')

    def test_invoice_form_status_uses_select2(self):
        response = self.client.get(reverse('invoice_create'))
        content = response.content.decode()
        self.assertIn('django-select2', content)

    def test_client_form_type_uses_select2(self):
        response = self.client.get(reverse('client_create'))
        self.assertContains(response, 'django-select2')

    def test_invoice_form_has_add_new_client_link(self):
        response = self.client.get(reverse('invoice_create'))
        content = response.content.decode()
        self.assertIn('target="_blank"', content)
        self.assertIn(reverse('client_create'), content)
        self.assertIn('add-new-link', content)

    def test_base_template_includes_select2_assets(self):
        response = self.client.get(reverse('invoice_create'))
        content = response.content.decode()
        self.assertIn('select2_min.css', content)
        self.assertIn('select2_min.js', content)
        self.assertIn('jquery_min.js', content)
