import nmap
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitor.models import NetworkHost, ProxmoxVM, HostedSite

class Command(BaseCommand):
    help = 'Scan network (nmap), Proxmox VMs, and Nginx Proxy Manager hosts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting full scan...'))

        # --- NPM API Scan ---
        self.stdout.write('NPM scan starting...')
        try:
            npm_url = 'http://192.168.20.129:81'
            auth_payload = {
                'identity': 'connell543@gmail.com',
                'secret': '4EVER&always'
            }
            token_resp = requests.post(f'{npm_url}/api/tokens', json=auth_payload, timeout=15)
            token_resp.raise_for_status()
            bearer_token = token_resp.json()['token']
            headers = {'Authorization': f'Bearer {bearer_token}'}
            hosts_resp = requests.get(f'{npm_url}/api/nginx/proxy-hosts', headers=headers, timeout=15)
            hosts_resp.raise_for_status()
            proxy_hosts = hosts_resp.json()

            updated_count = 0
            for host in proxy_hosts:
                domains = host.get('domain_names', [])
                if not domains:
                    continue
                main_domain = domains[0]
                obj, created = HostedSite.objects.update_or_create(
                    domain=main_domain,
                    defaults={
                        'forward_to': f"{host.get('forward_host', '')}:{host.get('forward_port', '')}",
                        'port': host.get('forward_port'),
                        'ssl_enabled': bool(host.get('meta', {}).get('ssl', {}).get('enabled', False)),
                        'status': 'active' if host.get('enabled', False) else 'disabled',
                        'last_scanned': timezone.now()
                    }
                )
                updated_count += 1
                action = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f"{action} site: {main_domain}"))

            self.stdout.write(f'NPM scan complete: {updated_count} sites processed')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'NPM scan failed: {type(e).__name__}: {str(e)}'))

        # --- Proxmox Scan ---
        self.stdout.write('Proxmox scan starting...')
        try:
            prox_url = 'https://192.168.7.118:8006/api2/json'
            headers = {
             'Authorization': 'PVEAPIToken=root@pam!nolimitadmin=1493843c-805f-480a-9a0f-ad0a0d54f93d'
            }
            self.stdout.write(f'Querying {prox_url}/cluster/resources...')
            resp = requests.get(f'{prox_url}/cluster/resources', headers=headers, verify=False, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            resources = data.get('data', [])
            self.stdout.write(f'Found {len(resources)} resources from Proxmox')

            count = 0
            for res in resources:
                if res.get('type') in ('qemu', 'lxc'):
                    obj, created = ProxmoxVM.objects.update_or_create(
                        vmid=res['vmid'],
                        defaults={
                            'name': res.get('name', 'unnamed'),
                            'status': res.get('status', 'unknown'),
                            'node': res.get('node', 'unknown'),
                            'cpu': res.get('cpu', 0) * 100 if res.get('cpu') else None,
                            'memory': res.get('mem', None),
                            'disk': res.get('maxdisk', 0) - res.get('disk', 0) if res.get('disk') is not None else None,
                            'uptime': res.get('uptime', None),
                            'last_updated': timezone.now()
                        }
                    )
                    count += 1
                    action = 'Created' if created else 'Updated'
                    self.stdout.write(self.style.SUCCESS(f"{action} VM: {obj.name} ({obj.status}) on {obj.node}"))

            self.stdout.write(f'Proxmox scan complete: {count} VMs processed')

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Proxmox request failed: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Proxmox scan error: {type(e).__name__}: {str(e)}'))

        # --- nmap Scan ---
        self.stdout.write('nmap scan starting...')
        try:
            scanner = nmap.PortScanner()
            subnets = ['192.168.7.1/24', '192.168.20.1/24']
            for subnet in subnets:
                self.stdout.write(f'Scanning subnet {subnet}...')
                scanner.scan(subnet, '22,80,443,81,8006', arguments='-T4 -Pn --host-timeout 20s')
                hosts_list = scanner.all_hosts()
                self.stdout.write(f'Found {len(hosts_list)} live hosts in {subnet}')

                for host_ip in hosts_list:
                    host_data = scanner[host_ip]
                    hostname = host_data.hostname() or 'unknown'
                    mac = host_data['addresses'].get('mac', 'unknown')
                    ports_open = []
                    if 'tcp' in host_data:
                        for port, info in host_data['tcp'].items():
                             if info['state'] == 'open':
                                 ports_open.append(port)
                obj, created = NetworkHost.objects.update_or_create(
                    ip=host_ip,
                    defaults={
                        'hostname': hostname,
                        'mac': mac,
                        'status': 'up',
                        'open_ports': ports_open,
                        'last_seen': timezone.now()
                    }   
                )
                action = 'Created' if created else 'Updated'
                self.stdout.write(self.style.SUCCESS(f"{action} host: {host_ip} ({hostname}) ports open: {ports_open}"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'nmap scan failed: {type(e).__name__}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Scan complete!'))