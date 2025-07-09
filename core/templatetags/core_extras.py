from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter
def slugify_tag(value):
    """Convert a tag string to a URL-friendly slug"""
    if not value:
        return ''
    return slugify(value.strip())