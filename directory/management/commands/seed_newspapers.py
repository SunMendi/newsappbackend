from django.core.management.base import BaseCommand

from directory.services import seed_default_newspapers


class Command(BaseCommand):
    help = "Seed default Bangladesh and international newspapers."

    def handle(self, *args, **options):
        result = seed_default_newspapers()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded newspapers: created={result['created']}, existing={result['existing']}"
            )
        )
