import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from core.base_models import BaseModel
from core.model_utils import generate_random_key

from core.choices import BlogPostStatus
from ask_hn_digest.utils import get_ask_hn_digest_logger
logger = get_ask_hn_digest_logger(__name__)


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.CharField(max_length=10, unique=True, default=generate_random_key)


class NewsletterSubscriber(BaseModel):
    email = models.EmailField(unique=True)
    added_to_buttondown = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    def add_newsletter_subscriber_to_buttondown(
        self,
        tags: list[str] = [],
        ip_address: str = None
    ):
        url = "https://api.buttondown.com/v1/subscribers"
        headers = {
          "Authorization": f"Token {settings.BUTTONDOWN_API_KEY}"
        }
        data = {
          "email_address": self.email,
          "type": "unactivated",
        }

        if len(tags) > 0:
            data["tags"] = tags

        if ip_address:
            data["ip_address"] = ip_address

        response = requests.request("POST", url, headers=headers, json=data)

        logger.info(
            "Newsletter subscription response",
            response_json=response.json(),
            response_text=response.text,
            status_code=response.status_code,
            email=self.email,
            tags=tags,
            ip_address=ip_address,
        )

        if response.status_code == 201:
            self.added_to_buttondown = True
            self.save()

            return True

        return False


class BlogPost(BaseModel):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=250)
    tags = models.TextField()
    content = models.TextField()
    icon = models.ImageField(upload_to="blog_post_icons/", blank=True)
    image = models.ImageField(upload_to="blog_post_images/", blank=True)
    status = models.CharField(
        max_length=10,
        choices=BlogPostStatus.choices,
        default=BlogPostStatus.DRAFT,
    )

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog_post", kwargs={"slug": self.slug})


class Feedback(BaseModel):
    profile = models.ForeignKey(
        Profile,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="feedback",
        help_text="The user who submitted the feedback",
    )
    feedback = models.TextField(
        help_text="The feedback text",
    )
    page = models.CharField(
        max_length=255,
        help_text="The page where the feedback was submitted",
    )

    def __str__(self):
        return f"{self.profile.user.email}: {self.feedback}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new:
            from django.conf import settings
            from django.core.mail import send_mail

            subject = "New Feedback Submitted"
            message = f"""
                New feedback was submitted:\n\n
                User: {self.profile.user.email if self.profile else 'Anonymous'}
                Feedback: {self.feedback}
                Page: {self.page}
            """
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [settings.DEFAULT_FROM_EMAIL]

            send_mail(subject, message, from_email, recipient_list, fail_silently=True)


class HNDiscussionSummary(BaseModel):
    discussion_id = models.BigIntegerField(unique=True, help_text="Hacker News discussion ID")
    comment_ids = models.JSONField(help_text="List of all comment IDs for this discussion")
    date_analyzed = models.DateTimeField(auto_now_add=True, help_text="Date and time when the discussion was analyzed")

    # for email
    short_summary = models.TextField(help_text="Short summary of the discussion")

    # for post
    slug = models.SlugField(max_length=250, unique=True, help_text="Slug for the blog post")
    title = models.CharField(max_length=250, help_text="Title of the blog post")
    description = models.TextField(blank=True, help_text="Description of the blog post")
    tags = models.TextField(blank=True, help_text="Tags for the blog post")
    long_summary = models.TextField(help_text="Long summary of the discussion")

    def __str__(self):
        return f"HN Discussion {self.discussion_id} analyzed on {self.date_analyzed}"

    def get_absolute_url(self):
        return reverse("blog_post", kwargs={"slug": self.slug})
