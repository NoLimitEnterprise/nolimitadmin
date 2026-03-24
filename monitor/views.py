from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import Node, NodeSnapshot, ProxmoxVM, SystemService, NetworkConnection, PacketCapture
from django.conf import settings

AGENT_SECRET = getattr(settings, 'AGENT_SECRET', '4EVER&always')

@csrf_exempt
def agent_post(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    if request.headers.get('X-Agent-Secret') != AGENT_SECRET:
        return JsonResponse({'error': 'Invalid or missing X-Agent-Secret header'}, status=403)

    try:
        payload = json.loads(request.body)
        hostname = payload.get('hostname')
        if not hostname:
            return JsonResponse({'error': 'hostname is required'}, status=400)

        # Update or create the Node
        node, created = Node.objects.get_or_create(hostname=hostname)
        node.is_online = True
        node.last_seen = timezone.now()
        if 'proxmox_version' in payload:
            node.proxmox_version = payload.get('proxmox_version', node.proxmox_version)
        node.save()

        # Save the FULL raw snapshot (this is where "every bit of data" lives)
        NodeSnapshot.objects.create(node=node, data=payload)

        # Normalize VMs / LXCs for fast dashboard queries
        for vm_data in payload.get('vms', []):
            ProxmoxVM.objects.update_or_create(
                node=node,
                vmid=vm_data['vmid'],
                defaults={
                    'name': vm_data.get('name', ''),
                    'vm_type': vm_data.get('type', 'lxc'),
                    'status': vm_data.get('status', 'unknown'),
                    'cpu': vm_data.get('cpu', 0.0),
                    'memory': vm_data.get('memory', 0),
                    'disk': vm_data.get('disk', 0),
                    'uptime': vm_data.get('uptime', 0),
                }
            )

        # Normalize running services
        for svc in payload.get('services', []):
            SystemService.objects.update_or_create(
                node=node,
                name=svc['name'],
                defaults={
                    'status': svc.get('status', 'unknown'),
                    'memory_bytes': svc.get('memory_bytes', 0),
                    'cpu_percent': svc.get('cpu_percent', 0.0),
                    'ports': svc.get('ports', []),
                }
            )

        # Save recent network connections (limit to avoid DB bloat)
        for conn in payload.get('connections', [])[:1000]:
            NetworkConnection.objects.create(
                node=node,
                src_ip=conn.get('src_ip'),
                dst_ip=conn.get('dst_ip'),
                src_port=conn.get('src_port'),
                dst_port=conn.get('dst_port'),
                protocol=conn.get('protocol', 'tcp'),
                state=conn.get('state', ''),
            )

        return JsonResponse({
            'status': 'success',
            'node': hostname,
            'snapshot_saved': True,
            'vms_updated': len(payload.get('vms', [])),
            'services_updated': len(payload.get('services', []))
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def start_packet_capture(request, hostname):
    """Trigger packet capture on vmbr0 (called from dashboard button)"""
    try:
        node = Node.objects.get(hostname=hostname)
        capture = PacketCapture.objects.create(
            node=node,
            started_at=timezone.now(),
            duration=120
        )
        # TODO: Later we can SSH or have the agent trigger tcpdump
        return JsonResponse({
            'status': 'capture_requested',
            'capture_id': capture.id,
            'hostname': hostname,
            'duration': 120,
            'interface': 'vmbr0'
        })
    except Node.DoesNotExist:
        return JsonResponse({'error': 'Node not found'}, status=404)
