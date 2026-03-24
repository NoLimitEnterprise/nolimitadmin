"""
URL configuration for dashboard project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('monitor/', include('monitor.urls')),   # ← This was missing
]
