from django.contrib import admin
from .models import Node, NodeSnapshot, ProxmoxVM, SystemService, NetworkConnection, PacketCapture

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'last_seen', 'is_online')
    list_filter = ('is_online',)

@admin.register(ProxmoxVM)
class ProxmoxVMAdmin(admin.ModelAdmin):
    list_display = ('name', 'vmid', 'vm_type', 'status', 'node')
    list_filter = ('node', 'vm_type', 'status')

@admin.register(SystemService)
class SystemServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'node')
    list_filter = ('node', 'status')

admin.site.register(NodeSnapshot)
admin.site.register(NetworkConnection)
admin.site.register(PacketCapture)
