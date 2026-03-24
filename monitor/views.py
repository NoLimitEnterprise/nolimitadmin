from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
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

        node, _ = Node.objects.get_or_create(hostname=hostname)
        node.is_online = True
        node.last_seen = timezone.now()
        if 'proxmox_version' in payload:
            node.proxmox_version = payload.get('proxmox_version', '')
        node.save()

        NodeSnapshot.objects.create(node=node, data=payload)

        # Normalize VMs
        for vm_data in payload.get('vms', []):
            ProxmoxVM.objects.update_or_create(
                node=node, vmid=vm_data.get('vmid'),
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

        # Normalize Services
        for svc in payload.get('services', []):
            SystemService.objects.update_or_create(
                node=node, name=svc.get('name', ''),
                defaults={
                    'status': svc.get('status', 'unknown'),
                    'memory_bytes': svc.get('memory_bytes', 0),
                    'cpu_percent': svc.get('cpu_percent', 0.0),
                    'ports': svc.get('ports', []),
                }
            )

        return JsonResponse({
            'status': 'success',
            'node': hostname,
            'snapshot_saved': True
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def start_packet_capture(request, hostname):
    node = get_object_or_404(Node, hostname=hostname)
    capture = PacketCapture.objects.create(node=node, started_at=timezone.now())
    return JsonResponse({'status': 'capture_requested', 'hostname': hostname})


def nodes_list(request):
    """Return all nodes for overview cards"""
    nodes = Node.objects.all().order_by('hostname')
    data = [{
        'hostname': n.hostname,
        'last_seen': n.last_seen.isoformat(),
        'is_online': n.is_online,
    } for n in nodes]
    return JsonResponse(data, safe=False)


def node_latest(request, hostname):
    """Return latest data for a node"""
    node = get_object_or_404(Node, hostname=hostname)
    latest = NodeSnapshot.objects.filter(node=node).order_by('-timestamp').first()
    
    if not latest:
        return JsonResponse({'vms': [], 'services': [], 'connections': []})

    data = latest.data.copy()
    data['vms'] = list(ProxmoxVM.objects.filter(node=node).values())
    data['services'] = list(SystemService.objects.filter(node=node).values())
    return JsonResponse(data)
