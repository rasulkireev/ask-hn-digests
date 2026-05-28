from urllib.parse import urlencode

from django.conf import settings
from django.templatetags.static import static

SITE_NAME = "Ask HN Digest"
DEFAULT_DESCRIPTION = "Get summaries of the most engaging discussions on Hacker News."
DEFAULT_FONT = "markerfelt"


def absolute_url(request, path_or_url):
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    return f"https://{request.get_host()}{path_or_url}"


def static_url(request, path):
    try:
        path_or_url = static(path)
    except ValueError:
        path_or_url = f"{settings.STATIC_URL}{path}"
    return absolute_url(request, path_or_url)


def clean_text(value):
    return " ".join(str(value or "").split())


def truncate_meta(value, max_length):
    text = clean_text(value)
    if len(text) <= max_length:
        return text

    truncated = text[: max_length - 3].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{truncated}..."


def discussion_description(summary, max_length=155):
    description = summary.description or summary.short_summary or DEFAULT_DESCRIPTION
    return truncate_meta(description, max_length)


def discussion_title(summary, max_length=42):
    return truncate_meta(summary.title, max_length)


def post_image_url(request, summary):
    image = getattr(summary, "image", None)
    try:
        if image:
            return absolute_url(request, image.url)
    except ValueError:
        pass
    return static_url(request, "vendors/images/logo.png")


def social_image_url(request, title, description, image_url=None, style="base", site="x"):
    params = {
        "site": site,
        "style": style,
        "font": DEFAULT_FONT,
        "title": clean_text(title),
        "subtitle": clean_text(description),
        "image_url": image_url or static_url(request, "vendors/images/logo.png"),
    }
    return f"https://osig.app/g?{urlencode(params)}"


def blog_post_schema(request, summary, url, image_url):
    return {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": clean_text(summary.title),
        "description": clean_text(summary.description or summary.short_summary or DEFAULT_DESCRIPTION),
        "image": image_url,
        "url": url,
        "datePublished": summary.created_at,
        "dateModified": summary.updated_at,
        "author": {
            "@type": "Person",
            "name": "Rasul Kireev",
            "url": "https://rasulkireev.com/",
        },
        "publisher": {
            "@type": "Organization",
            "name": SITE_NAME,
            "logo": {
                "@type": "ImageObject",
                "url": static_url(request, "vendors/images/logo.png"),
            },
        },
        "keywords": summary.get_tags_list(),
        "articleBody": clean_text(summary.long_summary),
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url,
        },
    }


def website_schema(request, url, name=SITE_NAME, description=DEFAULT_DESCRIPTION, image_url=None):
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": name,
        "description": clean_text(description),
        "thumbnailUrl": image_url or social_image_url(request, name, description, style="logo"),
        "url": url,
        "author": {
            "@type": "Person",
            "givenName": "Rasul",
            "familyName": "Kireev",
            "url": "https://rasulkireev.com/",
        },
    }
