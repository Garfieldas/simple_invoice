"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from app.views import (
    client_create,
    client_delete,
    client_edit,
    client_list,
    company_create,
    company_delete,
    company_edit,
    company_list,
    dashboard,
    invoice_create,
    invoice_delete,
    invoice_edit,
    invoice_list,
    profile_edit,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('select2/', include('django_select2.urls')),
    path('', dashboard, name='dashboard'),
    # Invoices
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/create/', invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/edit/', invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/delete/', invoice_delete, name='invoice_delete'),
    # Clients
    path('clients/', client_list, name='client_list'),
    path('clients/create/', client_create, name='client_create'),
    path('clients/<int:pk>/edit/', client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', client_delete, name='client_delete'),
    # Companies
    path('companies/', company_list, name='company_list'),
    path('companies/create/', company_create, name='company_create'),
    path('companies/<int:pk>/edit/', company_edit, name='company_edit'),
    path('companies/<int:pk>/delete/', company_delete, name='company_delete'),
    # Profile
    path('profile/', profile_edit, name='profile_edit'),
    path('', include('app.urls')),
]

if settings.DEBUG:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
