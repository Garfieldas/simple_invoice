from decimal import Decimal
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        return self.first_name or self.last_name or ''

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """Basic contact and payment details for the invoice sender."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    personal_code = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=200, blank=True)
    apartment_number = models.CharField(max_length=200, blank=True)
    bank_account = models.CharField(max_length=34, blank=True)  # IBAN max length
    bank_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return str(self.user)


class UserCompany(models.Model):
    """Optional company details — fill in if the sender is a registered business."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company')
    company_name = models.CharField(max_length=255)
    company_code = models.CharField(max_length=50)
    vat_code = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    apartment_number = models.CharField(max_length=20, blank=True)
    bank_account = models.CharField(max_length=34, blank=True)  # IBAN max length
    bank_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.company_name


class Client(models.Model):

    CLIENT_BUSINESS = 'business'
    CLIENT_INDIVIDUAL = 'individual'

    CLIENT_TYPES = [
    (CLIENT_BUSINESS, _('Business')),
    (CLIENT_INDIVIDUAL, _('Individual')),
    ]   

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    client_type = models.CharField(max_length=20, choices=CLIENT_TYPES, default=CLIENT_BUSINESS)
    name = models.CharField(max_length=255)
    company_code = models.CharField(max_length=50, blank=True)
    vat_code = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):

# --- Invoice statuses ---

    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_PAID = 'paid'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'

    INVOICE_STATUSES = [
    (STATUS_DRAFT, _('Draft')),
    (STATUS_SENT, _('Sent')),
    (STATUS_PAID, _('Paid')),
    (STATUS_OVERDUE, _('Overdue')),
    (STATUS_CANCELLED, _('Cancelled')),
    ]

    TAX_RATE_21 = '21.00'
    TAX_RATE_9 = '9.00'
    TAX_RATE_5 = '5.00'
    TAX_RATE_0 = '0.00'

    TAX_RATES = [
    (TAX_RATE_21, _('21%')),
    (TAX_RATE_9, _('9%')),
    (TAX_RATE_5, _('5%')),
    (TAX_RATE_0, _('0%')),
    ]

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='invoices')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='invoices')
    series = models.CharField(max_length=10, default='VF')
    number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=INVOICE_STATUSES, default=STATUS_DRAFT)
    issue_date = models.DateField()
    due_date = models.DateField()
    tax_enabled = models.BooleanField(default=True)
    tax_rate = models.CharField(max_length=5, choices=TAX_RATES, default=TAX_RATE_21, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'series', 'number')
        ordering = ('-issue_date', '-number')

    @property
    def invoice_number(self):
        return f'{self.series}-{self.number:06d}'

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def tax_amount(self):
        if not self.tax_enabled or not self.tax_rate:
            return Decimal('0.00')
        return (self.subtotal * Decimal(self.tax_rate) / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def total(self):
        return self.subtotal + self.tax_amount

    def __str__(self):
        return self.invoice_number


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=500)
    unit = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return self.description
