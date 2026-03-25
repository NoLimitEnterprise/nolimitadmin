from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
import json
from .models import Node, NodeSnapshot, ProxmoxVM, SystemService
from django.conf import settings

AGENT_SECRET = getattr(settings, 'AGENT_SECRET', '4EVER&always')

@csrf_exempt
def agent_post(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    if request.headers.get('X-Agent-Secret') != AGENT_SECRET:
        return JsonResponse({'error': 'Invalid secret'}, status=403)

    try:
        payload = json.loads(request.body)
        hostname = payload.get('hostname')
        if not hostname:
            return JsonResponse({'error': 'hostname required'}, status=400)

        node, _ = Node.objects.get_or_create(hostname=hostname)
        node.is_online = True
        node.last_seen = timezone.now()
        node.save()

        NodeSnapshot.objects.create(node=node, data=payload)

        return JsonResponse({'status': 'success', 'node': hostname})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def nodes_list(request):
    nodes = Node.objects.all().order_by('hostname')
    data = [{
        'hostname': n.hostname,
        'last_seen': n.last_seen.isoformat(),
        'is_online': n.is_online,
    } for n in nodes]
    return JsonResponse(data, safe=False)


def node_latest(request, hostname):
    node = get_object_or_404(Node, hostname=hostname)
    latest = NodeSnapshot.objects.filter(node=node).order_by('-timestamp').first()
    
    if not latest:
        return JsonResponse({'vms': [], 'services': []})

    data = latest.data.copy()
    data.setdefault('vms', [])
    data.setdefault('services', [])
    return JsonResponse(data)


def start_packet_capture(request, hostname):
    node = get_object_or_404(Node, hostname=hostname)
    return JsonResponse({'status': 'capture_requested', 'hostname': hostname})
