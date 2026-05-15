from django import template

register = template.Library()

@register.filter
def append_string(value, arg):
    return f'{value}{arg}'


@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='add_attributes')
def add_attributes(field, attributes):
    attrs = dict(attr.split('=') for attr in attributes.split())
    return field.as_widget(attrs=attrs)