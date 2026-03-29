import io
import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
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
from app.utils import amount_to_words_lt

# Register DejaVu Sans – it supports Lithuanian diacritics (ą, č, ę, ė, į, š, ų, ū, ž)
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

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
        if _is_htmx(request):
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': 'Invoice deleted successfully.'
            })
            return response
        messages.success(request, 'Invoice deleted successfully.')
        return redirect('invoice_list')
    context = {'object': invoice, 'title': 'Delete Invoice', 'cancel_url': 'invoice_list'}
    if _is_htmx(request):
        return render(request, 'crud/confirm_delete_partial.html', context)
    return render(request, 'crud/confirm_delete.html', context)


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('client', 'user'), pk=pk, user=request.user
    )
    items = invoice.items.all()
    profile = UserProfile.objects.filter(user=request.user).first()
    company = UserCompany.objects.filter(user=request.user).first()
    client = invoice.client

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('LTNormal', parent=styles['Normal'], fontName='DejaVuSans', fontSize=9, leading=12)
    style_bold = ParagraphStyle('LTBold', parent=style_normal, fontName='DejaVuSans-Bold')
    style_title = ParagraphStyle(
        'LTTitle', parent=styles['Title'], fontSize=14, fontName='DejaVuSans-Bold',
        alignment=1, spaceAfter=2 * mm,
    )
    style_small = ParagraphStyle('LTSmall', parent=style_normal, fontSize=8, leading=10)
    style_right = ParagraphStyle('LTRight', parent=style_normal, alignment=2)
    style_right_bold = ParagraphStyle(
        'LTRightBold', parent=style_right, fontName='DejaVuSans-Bold',
    )

    elements = []

    # --- Title ---
    elements.append(Paragraph("PVM SĄSKAITA FAKTŪRA", style_title))
    elements.append(
        Paragraph(
            f"Serija {invoice.series} Nr. {invoice.number:06d}",
            ParagraphStyle('Center', parent=style_normal, alignment=1),
        )
    )
    elements.append(Spacer(1, 4 * mm))

    # --- Dates ---
    date_data = [
        [
            Paragraph("Išrašymo data:", style_bold),
            Paragraph(invoice.issue_date.strftime("%Y-%m-%d"), style_normal),
            Paragraph("Apmokėti iki:", style_bold),
            Paragraph(invoice.due_date.strftime("%Y-%m-%d"), style_normal),
        ]
    ]
    date_table = Table(date_data, colWidths=[30 * mm, 35 * mm, 30 * mm, 35 * mm])
    date_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))
    elements.append(date_table)
    elements.append(Spacer(1, 5 * mm))

    # --- Seller / Buyer header ---
    seller_name = ""
    seller_lines = []
    if company:
        seller_name = company.company_name
        if company.company_code:
            seller_lines.append(f"Įmonės kodas: {company.company_code}")
        if company.vat_code:
            seller_lines.append(f"PVM kodas: {company.vat_code}")
        addr_parts = [p for p in [company.address, company.apartment_number, company.postal_code, company.city] if p]
        if addr_parts:
            seller_lines.append(f"Adresas: {', '.join(addr_parts)}")
        if company.bank_account:
            seller_lines.append(f"Banko sąskaita: {company.bank_account}")
        if company.bank_name:
            seller_lines.append(f"Bankas: {company.bank_name}")
    else:
        user = request.user
        seller_name = user.full_name or user.email
        if profile:
            if profile.personal_code:
                seller_lines.append(f"Asmens kodas: {profile.personal_code}")
            addr_parts = [p for p in [profile.address, profile.apartment_number, profile.postal_code, profile.city] if p]
            if addr_parts:
                seller_lines.append(f"Adresas: {', '.join(addr_parts)}")
            if profile.phone_number:
                seller_lines.append(f"Tel.: {profile.phone_number}")
            if profile.bank_account:
                seller_lines.append(f"Banko sąskaita: {profile.bank_account}")
            if profile.bank_name:
                seller_lines.append(f"Bankas: {profile.bank_name}")

    buyer_lines = []
    if client.company_code:
        buyer_lines.append(f"Įmonės kodas: {client.company_code}")
    if client.vat_code:
        buyer_lines.append(f"PVM kodas: {client.vat_code}")
    addr_parts = [p for p in [client.address, client.city] if p]
    if addr_parts:
        buyer_lines.append(f"Adresas: {', '.join(addr_parts)}")
    if client.email:
        buyer_lines.append(f"El. paštas: {client.email}")
    if client.phone_number:
        buyer_lines.append(f"Tel.: {client.phone_number}")

    seller_text = f"<b>{seller_name}</b><br/>" + "<br/>".join(seller_lines)
    buyer_text = f"<b>{client.name}</b><br/>" + "<br/>".join(buyer_lines)

    party_data = [
        [Paragraph("<b>Pardavėjas</b>", style_bold), Paragraph("<b>Pirkėjas</b>", style_bold)],
        [Paragraph(seller_text, style_small), Paragraph(buyer_text, style_small)],
    ]
    half = (A4[0] - 40 * mm) / 2
    party_table = Table(party_data, colWidths=[half, half])
    party_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.grey),
        ('LINEBETWEEN', (0, 0), (-1, -1), 0.5, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(party_table)
    elements.append(Spacer(1, 6 * mm))

    # --- Items table ---
    header = [
        Paragraph("<b>Nr.</b>", style_small),
        Paragraph("<b>Aprašymas</b>", style_small),
        Paragraph("<b>Mato vnt.</b>", style_small),
        Paragraph("<b>Kiekis</b>", style_small),
        Paragraph("<b>Kaina</b>", style_small),
        Paragraph("<b>Suma</b>", style_small),
    ]
    item_rows = [header]
    for idx, item in enumerate(items, start=1):
        item_rows.append([
            Paragraph(str(idx), style_small),
            Paragraph(item.description, style_small),
            Paragraph(item.unit or "-", style_small),
            Paragraph(str(item.quantity), style_small),
            Paragraph(f"{item.unit_price:.2f}", style_small),
            Paragraph(f"{item.line_total:.2f}", style_small),
        ])

    col_widths = [10 * mm, None, 18 * mm, 18 * mm, 22 * mm, 25 * mm]
    available = A4[0] - 40 * mm
    fixed = sum(w for w in col_widths if w is not None)
    col_widths[1] = available - fixed

    items_table = Table(item_rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4 * mm))

    # --- Totals ---
    subtotal = invoice.subtotal
    tax_amount = invoice.tax_amount
    total = invoice.total

    totals_data = [
        [Paragraph("Suma be PVM:", style_right), Paragraph(f"{subtotal:.2f} EUR", style_right_bold)],
    ]
    if invoice.tax_enabled and invoice.tax_rate:
        totals_data.append(
            [Paragraph(f"PVM ({invoice.tax_rate}%):", style_right), Paragraph(f"{tax_amount:.2f} EUR", style_right_bold)]
        )
    totals_data.append(
        [Paragraph("Bendra suma:", style_right), Paragraph(f"{total:.2f} EUR", style_right_bold)]
    )

    totals_table = Table(totals_data, colWidths=[available - 40 * mm, 40 * mm])
    totals_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 4 * mm))

    # --- Amount in words ---
    words = amount_to_words_lt(total)
    elements.append(Paragraph(f"Suma žodžiais: <b>{words}</b>", style_normal))

    # --- Notes ---
    if invoice.notes:
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(f"Pastabos: {invoice.notes}", style_normal))

    elements.append(Spacer(1, 10 * mm))

    # --- Signatures ---
    sig_data = [
        [Paragraph("Sąskaitą išrašė:", style_small), Paragraph("Sąskaitą gavo:", style_small)],
        [
            Paragraph("____________________", style_small),
            Paragraph("____________________", style_small),
        ],
        [
            Paragraph("(parašas, vardas, pavardė)", style_small),
            Paragraph("(parašas, vardas, pavardė)", style_small),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[half, half])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(sig_table)

    doc.build(elements)
    buf.seek(0)

    filename = f"saskaita_{invoice.invoice_number}.pdf"

    if request.GET.get('download') == '1':
        return FileResponse(buf, as_attachment=True, filename=filename, content_type='application/pdf')
    return FileResponse(buf, filename=filename, content_type='application/pdf')

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
        if _is_htmx(request):
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': 'Client deleted successfully.'
            })
            return response
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
        if _is_htmx(request):
            response = HttpResponse(status=200)
            response['HX-Trigger'] = json.dumps({
                'showMessage': 'Company deleted successfully.'
            })
            return response
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
