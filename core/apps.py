import posthog

from django.conf import settings
from django.apps import AppConfig
from ask_hn_digest.utils import get_ask_hn_digest_logger

logger = get_ask_hn_digest_logger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        import core.signals  # noqa
        

        if settings.ENVIRONMENT == "prod":
            posthog.api_key = settings.POSTHOG_API_KEY
            posthog.host = "https://us.i.posthog.com"
        
