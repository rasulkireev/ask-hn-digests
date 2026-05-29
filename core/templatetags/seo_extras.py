import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

register = template.Library()

_JSON_SCRIPT_ESCAPES = {
    ord(">"): "\\u003E",
    ord("<"): "\\u003C",
    ord("&"): "\\u0026",
}


@register.filter
def json_ld(value):
    json_value = json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=True)
    return mark_safe(json_value.translate(_JSON_SCRIPT_ESCAPES))
