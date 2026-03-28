from django.urls import path

from app import views

app_name = 'app'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
