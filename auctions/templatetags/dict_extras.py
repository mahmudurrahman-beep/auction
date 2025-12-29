# auctions/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Safely return dictionary.get(key). Works when dictionary is a QuerySet.values() result mapped to a dict.
    """
    try:
        return dictionary.get(key)
    except Exception:
        return None
