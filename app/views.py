from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

import json

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
        messages.success(request, 'Paskyra sėkmingai sukurta.')
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
        messages.success(request, 'Sąskaita sėkmingai sukurta.')
        return redirect('invoice_list')

    context = {'form': form, 'formset': formset, 'title': 'Sukurti sąskaitą'}
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
        messages.success(request, 'Sąskaita sėkmingai atnaujinta.')
        return redirect('invoice_list')

    context = {'form': form, 'formset': formset, 'title': 'Redaguoti sąskaitą', 'invoice': invoice}
    if _is_htmx(request):
        return render(request, 'crud/invoice_form_partial.html', context)
    return render(request, 'crud/invoice_form.html', context)


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    if request.method == 'POST':
        invoice.delete()
        if _is_htmx(request):
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': 'Sąskaita sėkmingai ištrinta.'
            })
            return response
        messages.success(request, 'Sąskaita sėkmingai ištrinta.')
        return redirect('invoice_list')
    context = {'object': invoice, 'title': 'Ištrinti sąskaitą', 'cancel_url': 'invoice_list'}
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
        messages.success(request, 'Klientas sėkmingai sukurtas.')
        return redirect('client_list')

    context = {'form': form, 'title': 'Pridėti klientą'}
    if _is_htmx(request):
        return render(request, 'crud/client_form_partial.html', context)
    return render(request, 'crud/client_form.html', context)


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Klientas sėkmingai atnaujintas.')
        return redirect('client_list')

    context = {'form': form, 'title': 'Redaguoti klientą', 'client': client}
    if _is_htmx(request):
        return render(request, 'crud/client_form_partial.html', context)
    return render(request, 'crud/client_form.html', context)


@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk, user=request.user)
    if request.method == 'POST':
        client.delete()
        if _is_htmx(request):
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': 'Klientas sėkmingai ištrintas.'
            })
            return response
        messages.success(request, 'Klientas sėkmingai ištrintas.')
        return redirect('client_list')
    context = {'object': client, 'title': 'Ištrinti klientą', 'cancel_url': 'client_list'}
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
        messages.success(request, 'Įmonė sėkmingai sukurta.')
        return redirect('company_list')

    context = {'form': form, 'title': 'Pridėti įmonę'}
    if _is_htmx(request):
        return render(request, 'crud/company_form_partial.html', context)
    return render(request, 'crud/company_form.html', context)


@login_required
def company_edit(request, pk):
    company = get_object_or_404(UserCompany, pk=pk, user=request.user)
    form = UserCompanyForm(request.POST or None, instance=company)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Įmonė sėkmingai atnaujinta.')
        return redirect('company_list')

    context = {'form': form, 'title': 'Redaguoti įmonę', 'company': company}
    if _is_htmx(request):
        return render(request, 'crud/company_form_partial.html', context)
    return render(request, 'crud/company_form.html', context)


@login_required
def company_delete(request, pk):
    company = get_object_or_404(UserCompany, pk=pk, user=request.user)
    if request.method == 'POST':
        company.delete()
        if _is_htmx(request):
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': 'Įmonė sėkmingai ištrinta.'
            })
            return response
        messages.success(request, 'Įmonė sėkmingai ištrinta.')
        return redirect('company_list')
    context = {'object': company, 'title': 'Ištrinti įmonę', 'cancel_url': 'company_list'}
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
        messages.success(request, 'Profilis sėkmingai atnaujintas.')
        return redirect('profile_edit')

    context = {'form': form, 'title': 'Jūsų profilis'}
    if _is_htmx(request):
        return render(request, 'crud/profile_form_partial.html', context)
    return render(request, 'crud/profile_form.html', context)


# ---------------------------------------------------------------------------
# Invoice PDF views
# ---------------------------------------------------------------------------

@login_required
def invoice_pdf(request, pk):
    """Generate a PDF for the given invoice (preview in browser)."""
    from decimal import Decimal
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    from app.utils import amount_to_words_lt

    invoice = get_object_or_404(
        Invoice.objects.select_related('client', 'user').prefetch_related('items'),
        pk=pk,
        user=request.user,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    style_normal = styles['Normal']
    style_heading = ParagraphStyle(
        'InvoiceHeading',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=6,
    )
    style_small = ParagraphStyle(
        'Small',
        parent=style_normal,
        fontSize=8,
        leading=10,
    )
    style_label = ParagraphStyle(
        'Label',
        parent=style_normal,
        fontSize=9,
        textColor=colors.HexColor('#666666'),
    )

    elements = []

    # --- Header ---
    elements.append(Paragraph(f'PVM SĄSKAITA FAKTŪRA {invoice.invoice_number}', style_heading))
    elements.append(Spacer(1, 4 * mm))

    # Seller / Buyer info
    seller_lines = []
    try:
        company = invoice.user.company
        seller_lines.append(f'<b>Pardavėjas:</b> {company.company_name}')
        if company.company_code:
            seller_lines.append(f'Įmonės kodas: {company.company_code}')
        if company.vat_code:
            seller_lines.append(f'PVM kodas: {company.vat_code}')
        if company.address or company.city:
            seller_lines.append(f'Adresas: {company.address} {company.city}'.strip())
        if company.bank_account:
            seller_lines.append(f'Banko sąskaita: {company.bank_account}')
        if company.bank_name:
            seller_lines.append(f'Bankas: {company.bank_name}')
    except Exception:
        seller_lines.append(f'<b>Pardavėjas:</b> {invoice.user.full_name or invoice.user.email}')

    buyer_lines = []
    buyer_lines.append(f'<b>Pirkėjas:</b> {invoice.client.name}')
    if invoice.client.company_code:
        buyer_lines.append(f'Įmonės kodas: {invoice.client.company_code}')
    if invoice.client.vat_code:
        buyer_lines.append(f'PVM kodas: {invoice.client.vat_code}')
    if invoice.client.address or invoice.client.city:
        buyer_lines.append(f'Adresas: {invoice.client.address} {invoice.client.city}'.strip())
    if invoice.client.email:
        buyer_lines.append(f'El. paštas: {invoice.client.email}')

    info_data = [[
        Paragraph('<br/>'.join(seller_lines), style_small),
        Paragraph('<br/>'.join(buyer_lines), style_small),
    ]]
    info_table = Table(info_data, colWidths=[doc.width / 2] * 2)
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # Dates and status
    date_info = (
        f'Išrašymo data: {invoice.issue_date}  |  '
        f'Apmokėjimo data: {invoice.due_date}'
    )
    elements.append(Paragraph(date_info, style_small))
    elements.append(Spacer(1, 6 * mm))

    # --- Items table ---
    header_row = ['Nr.', 'Aprašymas', 'Vnt.', 'Kiekis', 'Vnt. kaina', 'Suma']
    table_data = [header_row]

    items = invoice.items.all()
    for idx, item in enumerate(items, 1):
        table_data.append([
            str(idx),
            str(item.description),
            str(item.unit or ''),
            str(item.quantity),
            f'{item.unit_price:.2f}',
            f'{item.line_total:.2f}',
        ])

    col_widths = [
        doc.width * 0.06,
        doc.width * 0.38,
        doc.width * 0.10,
        doc.width * 0.12,
        doc.width * 0.17,
        doc.width * 0.17,
    ]

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6 * mm))

    # --- Totals ---
    subtotal = invoice.subtotal
    tax_amount = invoice.tax_amount
    total = invoice.total

    totals_data = [
        ['Tarpinė suma:', f'{subtotal:.2f} EUR'],
    ]
    if invoice.tax_enabled and invoice.tax_rate:
        totals_data.append([f'PVM ({invoice.tax_rate}%):', f'{tax_amount:.2f} EUR'])
    totals_data.append(['Bendra suma:', f'{total:.2f} EUR'])

    totals_table = Table(
        totals_data,
        colWidths=[doc.width * 0.80, doc.width * 0.20],
    )
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#111827')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#374151')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 6 * mm))

    # --- Amount in words ---
    words = amount_to_words_lt(total)
    elements.append(Paragraph(
        f'<b>Suma žodžiais:</b> {words}',
        style_normal,
    ))

    # --- Notes ---
    if invoice.notes:
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(f'<b>Pastabos:</b> {invoice.notes}', style_small))

    doc.build(elements)

    buf.seek(0)
    response = HttpResponse(buf.read(), content_type='application/pdf')
    download = request.GET.get('download')
    if download:
        response['Content-Disposition'] = (
            f'attachment; filename="saskaita_{invoice.invoice_number}.pdf"'
        )
    else:
        response['Content-Disposition'] = (
            f'inline; filename="saskaita_{invoice.invoice_number}.pdf"'
        )
    return response
