from allauth.account.signals import email_confirmed, user_signed_up
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# from django_q.tasks import async_task

# from core.tasks import add_email_to_buttondown
from core.models import Profile
from ask_hn_digest.utils import get_ask_hn_digest_logger

logger = get_ask_hn_digest_logger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)


    if instance.id == 1:
        # Use update() to avoid triggering the signal again
        User.objects.filter(id=1).update(is_staff=True, is_superuser=True)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()



@receiver(email_confirmed)
def add_email_to_buttondown_on_confirm(sender, **kwargs):
    logger.info(
        "Adding new user to buttondown newsletter, on email confirmation",
        kwargs=kwargs,
        sender=sender,
    )
    # async_task(add_email_to_buttondown, kwargs["email_address"], tag="user")
