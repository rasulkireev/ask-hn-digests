from django.contrib import sitemaps
from django.urls import reverse
from django.contrib.sitemaps import GenericSitemap

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
            "uses",
            "blog_posts",
        ]

    def location(self, item):
        """Get location for each item in the Sitemap

        Args:
            item (str): Item from the items function

        Returns:
            str: Url for the sitemap item
        """
        return reverse(item)

sitemaps = {
    "static": StaticViewSitemap,
    "blog": GenericSitemap(
        {
            "queryset": HNDiscussionSummary.objects.all(),
            "date_field": "created_at",
        },
        priority=0.85,
        protocol="https",
    ),
}
