from django.urls import path
from . import views

urlpatterns = [
    path('api/agent/', views.agent_post, name='agent_post'),
    path('api/capture/<str:hostname>/', views.start_packet_capture, name='packet_capture'),
    path('api/nodes/', views.nodes_list, name='nodes_list'),
    path('api/node/<str:hostname>/latest/', views.node_latest, name='node_latest'),
]
