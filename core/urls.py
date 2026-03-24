from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('auth/<slug:slug>/login/', views.dynamic_login, name='dynamic_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('log-fingerprint/', views.log_fingerprint, name='log_fingerprint'),
    path('monitor/', include('monitor.urls')),
    ]