from django.core.paginator import Paginator
from django.shortcuts import render

from app.models import Client, Invoice, UserCompany

ITEMS_PER_PAGE = 10


def _is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


def dashboard(request):
    if _is_htmx(request):
        return render(request, 'lists/dashboard_partial.html')
    return render(request, 'dashboard.html')


def invoice_list(request):
    invoices = Invoice.objects.select_related('client', 'user').all()

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


def client_list(request):
    clients = Client.objects.select_related('user').order_by('-created_at')

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


def company_list(request):
    companies = UserCompany.objects.select_related('user').order_by('company_name')

    paginator = Paginator(companies, ITEMS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    if _is_htmx(request):
        return render(request, 'lists/company_list_partial.html', context)
    return render(request, 'lists/company_list.html', context)
