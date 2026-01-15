"""
Custom template filters for Governance project
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary, return None if not found"""
    if not dictionary:
        return None
    return dictionary.get(key, None)


@register.filter
def dict_key(dictionary, key):
    """Safe dictionary get with a fallback default."""
    return dictionary.get(key, "") if dictionary else ""
