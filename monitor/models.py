from django.db import models

class NetworkHost(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    hostname = models.CharField(max_length=255, blank=True)
    mac = models.CharField(max_length=17, blank=True)
    status = models.CharField(max_length=20, default='unknown')  # up/down
    open_ports = models.JSONField(default=list, blank=True)  # e.g. [22, 80, 443]
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip} ({self.hostname or 'unknown'})"

class ProxmoxVM(models.Model):
    vmid = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)  # running/stopped
    node = models.CharField(max_length=100)
    cpu = models.FloatField(null=True, blank=True)  # %
    memory = models.BigIntegerField(null=True, blank=True)  # bytes used
    disk = models.BigIntegerField(null=True, blank=True)  # bytes used
    uptime = models.PositiveIntegerField(null=True, blank=True)  # seconds
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"VM {self.vmid}: {self.name} ({self.status})"

class HostedSite(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    forward_to = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(null=True, blank=True)
    ssl_enabled = models.BooleanField(default=False)
    ssl_expiry = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default='unknown')
    last_scanned = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.domain