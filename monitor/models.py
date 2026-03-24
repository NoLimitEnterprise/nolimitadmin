from django.db import models
from django.utils import timezone
import uuid

class Node(models.Model):
    hostname = models.CharField(max_length=100, unique=True, help_text="km01, km02, etc.")
    last_seen = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=True)
    proxmox_version = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.hostname

class NodeSnapshot(models.Model):
    """Raw full snapshot - this is where we store EVERY metric the agent sends"""
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='snapshots')
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField()   # cpu, ram, vms, lxcs, services, network, open ports, etc.

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['timestamp'])]

    def __str__(self):
        return f"{self.node.hostname} @ {self.timestamp}"

class ProxmoxVM(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='vms')
    vmid = models.IntegerField()
    name = models.CharField(max_length=200, blank=True)
    vm_type = models.CharField(max_length=10, choices=[('qemu', 'QEMU'), ('lxc', 'LXC')])
    status = models.CharField(max_length=20, blank=True)
    cpu = models.FloatField(default=0)
    memory = models.BigIntegerField(default=0)   # bytes
    disk = models.BigIntegerField(default=0)
    uptime = models.BigIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('node', 'vmid')

    def __str__(self):
        return f"{self.name} ({self.vmid}) on {self.node}"

class SystemService(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=50)
    memory_bytes = models.BigIntegerField(default=0)
    cpu_percent = models.FloatField(default=0)
    ports = models.JSONField(default=list)
    last_updated = models.DateTimeField(auto_now=True)

class NetworkConnection(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='connections')
    timestamp = models.DateTimeField(default=timezone.now)
    src_ip = models.GenericIPAddressField()
    dst_ip = models.GenericIPAddressField()
    src_port = models.IntegerField(null=True, blank=True)
    dst_port = models.IntegerField(null=True, blank=True)
    protocol = models.CharField(max_length=10, default='tcp')
    state = models.CharField(max_length=20, blank=True)

class PacketCapture(models.Model):
    node = models.ForeignKey(Node, on_delete=models.CASCADE)
    started_at = models.DateTimeField()
    duration = models.IntegerField(default=120)
    summary = models.JSONField(default=dict)   # top talkers, packet count, etc.
    pcap_path = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return f"Capture {self.node} @ {self.started_at}"
