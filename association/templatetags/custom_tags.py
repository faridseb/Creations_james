# myapp/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def add_months(mois_actuel, offset):
    return mois_actuel + offset



@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, {})


