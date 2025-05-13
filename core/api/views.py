from django.http import HttpRequest
from ninja import NinjaAPI

from core.api.auth import MultipleAuthSchema
from core.models import BlogPost, Feedback, NewsletterSubscriber
from core.api.schemas import (
    NewsletterSubscribeIn,
    NewsletterSubscribeOut,
    SubmitFeedbackIn,
    SubmitFeedbackOut,
    BlogPostIn,
    BlogPostOut,
)

from ask_hn_digest.utils import get_ask_hn_digest_logger

logger = get_ask_hn_digest_logger(__name__)

api = NinjaAPI(auth=MultipleAuthSchema(), csrf=True)

@api.post("/submit-feedback", response=SubmitFeedbackOut)
def submit_feedback(request: HttpRequest, data: SubmitFeedbackIn):
    profile = request.auth
    try:
        Feedback.objects.create(profile=profile, feedback=data.feedback, page=data.page)
        return {"status": True, "message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error("Failed to submit feedback", error=str(e), profile_id=profile.id)
        return {"status": False, "message": "Failed to submit feedback. Please try again."}


@api.post("/blog-posts/submit", response=BlogPostOut)
def submit_blog_post(request: HttpRequest, data: BlogPostIn):
    try:
        BlogPost.objects.create(
            title=data.title,
            description=data.description,
            slug=data.slug,
            tags=data.tags,
            content=data.content,
            status=data.status,
            # icon and image are ignored for now (file upload not handled)
        )
        return BlogPostOut(status="success", message="Blog post submitted successfully.")
    except Exception as e:
        return BlogPostOut(status="failure", message=f"Failed to submit blog post: {str(e)}")


@api.post("/newsletter/subscribe/", response=NewsletterSubscribeOut, auth=None)
def newsletter_subscribe(request: HttpRequest, data: NewsletterSubscribeIn):
    subscriber, created = NewsletterSubscriber.objects.get_or_create(email=data.email)

    if not created:
        return NewsletterSubscribeOut(
            status="failure",
            message="You are already subscribed to the newsletter."
        )

    added_to_buttondown = subscriber.add_newsletter_subscriber_to_buttondown()
    if not added_to_buttondown:
        return NewsletterSubscribeOut(
            status="failure",
            message="Failed to subscribe to the newsletter. Please try again later."
        )

    return NewsletterSubscribeOut(
        status="success",
        message="Subscribed successfully! Please check your email to confirm \
          your subscription and start receiving your weekly digest."
    )
