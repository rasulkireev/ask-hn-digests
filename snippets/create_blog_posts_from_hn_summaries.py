from tqdm import tqdm

from core.choices import BlogPostStatus
from core.models import BlogPost, HNDiscussionSummary

summaries = HNDiscussionSummary.objects.all().order_by("-date_analyzed")
total = summaries.count()

if total == 0:
    print("No summaries found.")
else:
    print(f"Found {total} summaries. Creating blog posts...")

    created_count = 0
    skipped_count = 0
    error_count = 0

    with tqdm(total=total, desc="Creating blog posts") as pbar:
        for summary in summaries.iterator():
            if BlogPost.objects.filter(slug=summary.slug).exists():
                tqdm.write(f"Skipping {summary.slug} - blog post already exists")
                skipped_count += 1
                pbar.update(1)
                continue

            try:
                BlogPost.objects.create(
                    title=summary.title,
                    description=summary.description or "",
                    slug=summary.slug,
                    tags=summary.tags or "",
                    content=summary.long_summary,
                    status=BlogPostStatus.PUBLISHED,
                    hn_discussion_summary=summary,
                )
                created_count += 1
                tqdm.write(f"Created blog post: {summary.title}")
            except Exception as e:
                error_count += 1
                tqdm.write(f"Error creating blog post for {summary.slug}: {str(e)}")

            pbar.update(1)

    print("\nSummary:")
    print(f"Created: {created_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Errors: {error_count}")
