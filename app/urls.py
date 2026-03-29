from django.urls import path

from app.forms import CustomPasswordResetForm, CustomSetPasswordForm
from app.views import (
    client_create,
    client_delete,
    client_edit,
    client_list,
    company_create,
    company_delete,
    company_edit,
    company_list,
    create_invoice_pdf,
    dashboard,
    invoice_create,
    invoice_delete,
    invoice_edit,
    invoice_list,
    login_view,
    logout_view,
    profile_edit,
    register_view,
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Dashboard
    path('', dashboard, name='dashboard'),
    # Auth
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='auth/password_reset.html',
            form_class=CustomPasswordResetForm,
            email_template_name='auth/password_reset_email.html',
            subject_template_name='auth/password_reset_subject.txt',
            success_url='/password-reset/done/',
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='auth/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='auth/password_reset_confirm.html',
            form_class=CustomSetPasswordForm,
            success_url='/password-reset-complete/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='auth/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    # Invoices
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/create/', invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/edit/', invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/delete/', invoice_delete, name='invoice_delete'),
    path('invoices/<str:invoice_pk>/pdf/', create_invoice_pdf, name='create_invoice_pdf'),
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
]
