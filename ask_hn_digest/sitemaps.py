from django.contrib import sitemaps
from django.contrib.sitemaps import GenericSitemap
from django.db.models import Max
from django.urls import reverse

from core.models import HNDiscussionSummary


class StaticViewSitemap(sitemaps.Sitemap):
    """Generate Sitemap for the site"""

    priority = 0.9
    protocol = "https"

    def items(self):
        """Identify items that will be in the Sitemap

        Returns:
            List: urlNames that will be in the Sitemap
        """
        return [
            "home",
            "blog_posts",
            "tag_list",
        ]

    def location(self, item):
        """Get location for each item in the Sitemap

        Args:
            item (str): Item from the items function

        Returns:
            str: Url for the sitemap item
        """
        return reverse(item)


class TagSitemap(sitemaps.Sitemap):
    """Generate sitemap entries for public tag archive pages."""

    priority = 0.6
    protocol = "https"

    def items(self):
        return HNDiscussionSummary.get_all_tags_with_counts().annotate(
            latest_summary_updated_at=Max("summaries__updated_at")
        )

    def location(self, item):
        return reverse("tag_detail", kwargs={"tag_slug": item.slug})

    def lastmod(self, item):
        return item.latest_summary_updated_at or item.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "tags": TagSitemap,
    "blog": GenericSitemap(
        {
            "queryset": HNDiscussionSummary.objects.all(),
            "date_field": "updated_at",
        },
        priority=0.85,
        protocol="https",
    ),
}
