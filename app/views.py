from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from app.forms import (
    ClientForm,
    InvoiceForm,
    InvoiceItemFormSet,
    LoginForm,
    RegisterForm,
    UserCompanyForm,
    UserProfileForm,
)
from app.models import Client, Invoice, UserCompany, UserProfile

ITEMS_PER_PAGE = 10


def _is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')
    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Account created successfully.')
        return redirect('dashboard')
    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    if _is_htmx(request):
        return render(request, 'lists/dashboard_partial.html')
    return render(request, 'dashboard.html')


# ---------------------------------------------------------------------------
# Invoice views
# ---------------------------------------------------------------------------

@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('client', 'user').filter(user=request.user)

    status = request.GET.get('status')
    if status:
        invoices = invoices.filter(status=status)

    paginator = Paginator(invoices, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_choices': Invoice.INVOICE_STATUSES,
        'current_status': status or '',
    }

    if _is_htmx(request):
        return render(request, 'lists/invoice_list_partial.html', context)
    return render(request, 'lists/invoice_list.html', context)


@login_required
def invoice_create(request):
    form = InvoiceForm(request.POST or None)
    form.fields['client'].queryset = Client.objects.filter(user=request.user)
    formset = InvoiceItemFormSet(request.POST or None)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        invoice = form.save(commit=False)
        invoice.user = request.user
        invoice.save()
        formset.instance = invoice
        formset.save()
        messages.success(request, 'Invoice created successfully.')
        return redirect('invoice_list')

    context = {'form': form, 'formset': formset, 'title': 'Create Invoice'}
    if _is_htmx(request):
        return render(request, 'crud/invoice_form_partial.html', context)
    return render(request, 'crud/invoice_form.html', context)


@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    form = InvoiceForm(request.POST or None, instance=invoice)
    form.fields['client'].queryset = Client.objects.filter(user=request.user)
    formset = InvoiceItemFormSet(request.POST or None, instance=invoice)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, 'Invoice updated successfully.')
        return redirect('invoice_list')

    context = {'form': form, 'formset': formset, 'title': 'Edit Invoice', 'invoice': invoice}
    if _is_htmx(request):
        return render(request, 'crud/invoice_form_partial.html', context)
    return render(request, 'crud/invoice_form.html', context)


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully.')
        return redirect('invoice_list')
    context = {'object': invoice, 'title': 'Delete Invoice', 'cancel_url': 'invoice_list'}
    if _is_htmx(request):
        return render(request, 'crud/confirm_delete_partial.html', context)
    return render(request, 'crud/confirm_delete.html', context)


# ---------------------------------------------------------------------------
# Client views
# ---------------------------------------------------------------------------

@login_required
def client_list(request):
    clients = Client.objects.filter(user=request.user).order_by('-created_at')

    client_type = request.GET.get('client_type')
    if client_type:
        clients = clients.filter(client_type=client_type)

    paginator = Paginator(clients, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'client_type_choices': Client.CLIENT_TYPES,
        'current_client_type': client_type or '',
    }

    if _is_htmx(request):
        return render(request, 'lists/client_list_partial.html', context)
    return render(request, 'lists/client_list.html', context)


@login_required
def client_create(request):
    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        client = form.save(commit=False)
        client.user = request.user
        client.save()
        messages.success(request, 'Client created successfully.')
        return redirect('client_list')

    context = {'form': form, 'title': 'Add Client'}
    if _is_htmx(request):
        return render(request, 'crud/client_form_partial.html', context)
    return render(request, 'crud/client_form.html', context)


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Client updated successfully.')
        return redirect('client_list')

    context = {'form': form, 'title': 'Edit Client', 'client': client}
    if _is_htmx(request):
        return render(request, 'crud/client_form_partial.html', context)
    return render(request, 'crud/client_form.html', context)


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    if request.method == 'POST':
        client.delete()
        messages.success(request, 'Client deleted successfully.')
        return redirect('client_list')
    context = {'object': client, 'title': 'Delete Client', 'cancel_url': 'client_list'}
    if _is_htmx(request):
        return render(request, 'crud/confirm_delete_partial.html', context)
    return render(request, 'crud/confirm_delete.html', context)


# ---------------------------------------------------------------------------
# Company views
# ---------------------------------------------------------------------------

@login_required
def company_list(request):
    companies = UserCompany.objects.filter(user=request.user).order_by('company_name')

    paginator = Paginator(companies, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    if _is_htmx(request):
        return render(request, 'lists/company_list_partial.html', context)
    return render(request, 'lists/company_list.html', context)


@login_required
def company_create(request):
    form = UserCompanyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        company = form.save(commit=False)
        company.user = request.user
        company.save()
        messages.success(request, 'Company created successfully.')
        return redirect('company_list')

    context = {'form': form, 'title': 'Add Company'}
    if _is_htmx(request):
        return render(request, 'crud/company_form_partial.html', context)
    return render(request, 'crud/company_form.html', context)


@login_required
def company_edit(request, pk):
    company = get_object_or_404(UserCompany, pk=pk, user=request.user)
    form = UserCompanyForm(request.POST or None, instance=company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Company updated successfully.')
        return redirect('company_list')

    context = {'form': form, 'title': 'Edit Company', 'company': company}
    if _is_htmx(request):
        return render(request, 'crud/company_form_partial.html', context)
    return render(request, 'crud/company_form.html', context)


@login_required
def company_delete(request, pk):
    company = get_object_or_404(UserCompany, pk=pk, user=request.user)
    if request.method == 'POST':
        company.delete()
        messages.success(request, 'Company deleted successfully.')
        return redirect('company_list')
    context = {'object': company, 'title': 'Delete Company', 'cancel_url': 'company_list'}
    if _is_htmx(request):
        return render(request, 'crud/confirm_delete_partial.html', context)
    return render(request, 'crud/confirm_delete.html', context)


# ---------------------------------------------------------------------------
# User Profile views
# ---------------------------------------------------------------------------

@login_required
def profile_edit(request):
    profile, _created = UserProfile.objects.get_or_create(user=request.user)
    form = UserProfileForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile_edit')

    context = {'form': form, 'title': 'Your Profile'}
    if _is_htmx(request):
        return render(request, 'crud/profile_form_partial.html', context)
    return render(request, 'crud/profile_form.html', context)
