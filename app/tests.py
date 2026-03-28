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
