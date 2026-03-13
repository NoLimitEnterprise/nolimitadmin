from django.contrib import admin
from .models import NetworkHost, ProxmoxVM, HostedSite

@admin.register(NetworkHost)
class NetworkHostAdmin(admin.ModelAdmin):
    list_display = ('ip', 'hostname', 'status', 'open_ports', 'last_seen')
    search_fields = ('ip', 'hostname')

@admin.register(ProxmoxVM)
class ProxmoxVMAdmin(admin.ModelAdmin):
    list_display = ('vmid', 'name', 'status', 'node', 'cpu', 'memory', 'last_updated')

@admin.register(HostedSite)
class HostedSiteAdmin(admin.ModelAdmin):
    list_display = ('domain', 'forward_to', 'ssl_enabled', 'status', 'last_scanned')