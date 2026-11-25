from django.core.management.base import BaseCommand

from feed.services import seed_default_poll, sync_all_active_portals


class Command(BaseCommand):
    help = "Sync latest news from all active TenantPortals and ensure an active poll exists."

    def handle(self, *args, **options):
        seed_default_poll()
        summary = sync_all_active_portals()
        self.stdout.write(self.style.SUCCESS(f"Sync complete: {summary}"))
