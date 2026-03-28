from django.shortcuts import render


def dashboard(request):
    stats = [
        {
            'label': 'Total Invoices',
            'value': '0',
            'icon': 'document',
            'color': 'blue',
        },
        {
            'label': 'Paid',
            'value': '0',
            'icon': 'check-circle',
            'color': 'green',
        },
        {
            'label': 'Pending',
            'value': '0',
            'icon': 'clock',
            'color': 'yellow',
        },
        {
            'label': 'Total Revenue',
            'value': '$0.00',
            'icon': 'currency',
            'color': 'blue',
        },
    ]
    breadcrumb = [
        {'label': 'Dashboard'},
    ]
    return render(request, 'app/dashboard.html', {'stats': stats, 'breadcrumb': breadcrumb})
