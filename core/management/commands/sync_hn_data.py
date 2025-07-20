from django.core.management.base import BaseCommand
from django_q.tasks import async_task

from ask_hn_digest.utils import get_ask_hn_digest_logger

logger = get_ask_hn_digest_logger(__name__)


class Command(BaseCommand):
    help = "Syncs Hacker News data using async processing via django_q2."

    def handle(self, *args, **options):
        logger.info("Queuing HN data sync task")

        # Queue the async task
        task_id = async_task(
            "core.tasks.sync_hn_data_async",
            group="HN Data Sync",
            timeout=24 * 60 * 60,  # 24 hours timeout
        )

        self.stdout.write(self.style.SUCCESS(f"✅ HN data sync task queued with ID: {task_id}"))

        logger.info("HN data sync task queued successfully", task_id=task_id)
