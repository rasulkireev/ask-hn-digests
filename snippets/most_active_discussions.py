from django.db.models import Func, IntegerField

from core.models import HNDiscussionSummary

print("Fetching top 10 most active discussions...")

# Annotate with comment count and order by it
most_active_discussions = (
    HNDiscussionSummary.objects.annotate(
        comment_count=Func(
            "comment_ids",
            function="jsonb_array_length",
            output_field=IntegerField(),
        )
    )
    .order_by("-comment_count")
    .values("discussion_id", "discussion_title", "comment_count")[:10]
)

if not most_active_discussions:
    print("No discussions found.")
else:
    print("-" * 30)
    for discussion in most_active_discussions:
        print(
            f"ID: {discussion['discussion_id']} | "
            f"Comments: {discussion['comment_count']} | "
            f"Title: {discussion['discussion_title']}"
        )
    print("-" * 30)
