from django.contrib import admin

from core.models import BlogPost, HNDiscussionSummary, NewsletterSubscriber

admin.site.register(BlogPost)
admin.site.register(HNDiscussionSummary)
admin.site.register(NewsletterSubscriber)
