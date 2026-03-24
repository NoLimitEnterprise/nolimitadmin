#!/usr/bin/env python3
import json
import time
import subprocess
import psutil
import requests
import socket
from datetime import datetime, timezone

AGENT_SECRET = "4EVER&always"
DASHBOARD_URL = "http://100.79.92.20/monitor/api/agent/"

def get_proxmox_data():
    data = {
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "proxmox_version": subprocess.getoutput("pveversion -v 2>/dev/null || echo 'N/A'"),
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
            "load_avg": [float(x) for x in open('/proc/loadavg').read().split()[:3]],
        },
        "vms": [],
        "services": [],
        "connections": [],
    }

    # Proxmox VMs and LXCs (simplified for now)
    try:
        for cmd, vtype in [("qm list", "qemu"), ("pct list", "lxc")]:
            output = subprocess.getoutput(cmd + " 2>/dev/null")
            for line in output.splitlines()[1:]:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        data["vms"].append({
                            "vmid": int(parts[0]),
                            "name": parts[1],
                            "type": vtype,
                            "status": parts[2],
                            "cpu": float(parts[3]) if len(parts) > 3 else 0.0,
                        })
    except:
        pass

    # Services
    try:
        services = subprocess.getoutput("systemctl list-units --type=service --state=running --no-legend").splitlines()
        for line in services:
            if line.strip():
                name = line.split()[0]
                data["services"].append({
                    "name": name,
                    "status": "active",
                    "memory_bytes": 0,
                    "cpu_percent": 0.0,
                    "ports": [],
                })
    except:
        pass

    return data


if __name__ == "__main__":
    print(f"🚀 Agent started on {socket.gethostname()} - sending every 10s to {DASHBOARD_URL}")
    while True:
        try:
            payload = get_proxmox_data()
            headers = {
                'X-Agent-Secret': AGENT_SECRET,
                'Content-Type': 'application/json'
            }
            response = requests.post(DASHBOARD_URL, json=payload, headers=headers, timeout=10)
            print(f"[{datetime.now()}] Sent to dashboard - Status: {response.status_code} - Node: {payload.get('hostname')}")
            if response.status_code != 200:
                print("Response body:", response.text[:500])
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")

        time.sleep(10)
