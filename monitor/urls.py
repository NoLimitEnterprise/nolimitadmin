from django.urls import path
from . import views

urlpatterns = [
    path('api/agent/', views.agent_post, name='agent_post'),
    path('api/capture/<str:hostname>/', views.start_packet_capture, name='packet_capture'),
]
