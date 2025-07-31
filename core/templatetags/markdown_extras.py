import markdown as md
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
@stringfilter
def markdown(value):
    md_instance = md.Markdown(extensions=["tables"])
    html = md_instance.convert(value)
    return mark_safe(html)


@register.filter
@stringfilter
def replace_quotes(value):
    return value.replace('"', "'")


@register.filter
@stringfilter
def split(value, delimiter=","):
    """Split a string by the given delimiter and return a list"""
    if not value:
        return []
    return [item.strip() for item in value.split(delimiter) if item.strip()]
