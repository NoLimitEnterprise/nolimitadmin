#!/usr/bin/env python3
import json
import time
import subprocess
import psutil
import requests
import socket
from datetime import datetime

AGENT_SECRET = "4EVER&always"   # MUST MATCH settings.py AGENT_SECRET
DASHBOARD_URL = "https://nolimitadmin.com/monitor/api/agent/"   # CHANGE TO YOUR REAL URL or http://100.79.92.20/monitor/api/agent/

def get_proxmox_data():
    """Collect EVERYTHING possible from Proxmox + Ubuntu"""
    data = {
        "hostname": socket.gethostname(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "proxmox_version": subprocess.getoutput("pveversion -v 2>/dev/null || echo 'not_proxmox'"),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "percent": psutil.disk_usage('/').percent,
            },
            "load_avg": [x for x in open('/proc/loadavg').read().split()[:3]],
        },
        "vms": [],
        "services": [],
        "connections": [],
    }

    # === Proxmox VMs & LXCs ===
    try:
        vms = subprocess.getoutput("qm list 2>/dev/null || echo ''").splitlines()
        for line in vms[1:]:  # skip header
            if line.strip():
                parts = line.split()
                if len(parts) >= 4:
                    data["vms"].append({
                        "vmid": int(parts[0]),
                        "name": parts[1],
                        "type": "qemu",
                        "status": parts[2],
                        "cpu": float(parts[3]) if len(parts) > 3 else 0,
                    })
    except:
        pass

    try:
        lxcs = subprocess.getoutput("pct list 2>/dev/null || echo ''").splitlines()
        for line in lxcs[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    data["vms"].append({
                        "vmid": int(parts[0]),
                        "name": parts[1],
                        "type": "lxc",
                        "status": parts[2],
                    })
    except:
        pass

    # === All systemd services with memory/CPU ===
    try:
        services = subprocess.getoutput("systemctl list-units --type=service --state=running --no-legend").splitlines()
        for svc in services:
            name = svc.split()[0]
            status = "active"
            # Get memory (rough)
            mem = subprocess.getoutput(f"systemctl show {name} -p MemoryCurrent --value 2>/dev/null || echo 0")
            data["services"].append({
                "name": name,
                "status": status,
                "memory_bytes": int(mem) if mem.isdigit() else 0,
                "cpu_percent": 0.0,  # can enhance with ps
                "ports": [],  # can add ss -tlnp later
            })
    except:
        pass

    # === Network connections on vmbr0 (src/dst) ===
    try:
        conns = subprocess.getoutput("ss -tuln 2>/dev/null | grep -E '0.0.0.0|::'").splitlines()
        for line in conns:
            parts = line.split()
            if len(parts) >= 5:
                data["connections"].append({
                    "src_ip": parts[3].split(':')[0] if ':' in parts[3] else parts[3],
                    "dst_ip": "0.0.0.0",
                    "src_port": int(parts[3].split(':')[-1]) if ':' in parts[3] else None,
                    "dst_port": None,
                    "protocol": "tcp" if parts[0].startswith('tcp') else "udp",
                    "state": "LISTEN",
                })
    except:
        pass

    return data

if __name__ == "__main__":
    while True:
        try:
            payload = get_proxmox_data()
            headers = {
                'X-Agent-Secret': AGENT_SECRET,
                'Content-Type': 'application/json'
            }
            response = requests.post(DASHBOARD_URL, json=payload, headers=headers, timeout=10)
            print(f"[{datetime.now()}] Sent to dashboard - Status: {response.status_code} - Node: {payload['hostname']}")
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")

        time.sleep(10)   # every 10 seconds
