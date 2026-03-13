import time
import schedule
from django.core.management.base import BaseCommand 
from django.core import management

class Command(BaseCommand):
    help = 'Runs continuous network/Proxmox/NPM scans every 5 minutes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting scan loop... Press Ctrl+C to stop.'))
        schedule.every(5).minutes.do(lambda: management.call_command('scan_network'))

        while True:
            schedule.run_pending()
            time.sleep(60)