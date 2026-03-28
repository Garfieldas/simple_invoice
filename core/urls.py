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

from app.views import client_list, company_list, dashboard, invoice_list

urlpatterns = [
    path('admin/', admin.site.urls),
    path('select2/', include('django_select2.urls')),
    path('', dashboard, name='dashboard'),
    path('invoices/', invoice_list, name='invoice_list'),
    path('clients/', client_list, name='client_list'),
    path('companies/', company_list, name='company_list'),
    path('', include('app.urls')),
]

if settings.DEBUG:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
