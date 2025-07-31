from django.contrib import admin
from django_q.tasks import async_task

from core.models import BlogPost, HNDiscussionSummary, NewsletterSubscriber
from core.utils import send_to_typefully


@admin.action(description="Send selected summary threads to Typefully")
def send_to_typefully_action(modeladmin, request, queryset):
    successful_sends = 0
    for summary in queryset:
        if summary.twitter_thread:
            send_to_typefully(summary.twitter_thread)
            successful_sends += 1
    if successful_sends > 0:
        modeladmin.message_user(
            request, f"{successful_sends} summaries have been sent to Typefully."
        )


@admin.action(description="Generate twitter thread (and send to Typefully) for selected summaries")
def schedule_twitter_thread_generation(modeladmin, request, queryset):
    for summary in queryset:
        async_task(
            "core.tasks.generate_twitter_thread",
            summary,
            group="Generate Twitter Thread",
        )
    modeladmin.message_user(
        request,
        f"Scheduled Twitter thread generation for {queryset.count()} summaries.",
    )


@admin.action(description="Generate single tweet for selected summaries")
def schedule_single_tweet_generation(modeladmin, request, queryset):
    for summary in queryset:
        async_task(
            "core.tasks.generate_single_tweet",
            summary,
            group="Generate Single Tweet",
        )
    modeladmin.message_user(
        request, f"Scheduled single tweet generation for {queryset.count()} summaries."
    )


class HNDiscussionSummaryAdmin(admin.ModelAdmin):
    actions = [
        send_to_typefully_action,
        schedule_twitter_thread_generation,
        schedule_single_tweet_generation,
    ]


admin.site.register(BlogPost)
admin.site.register(HNDiscussionSummary, HNDiscussionSummaryAdmin)
admin.site.register(NewsletterSubscriber)
