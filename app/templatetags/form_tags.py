from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS classes to a form field widget."""
    existing = field.field.widget.attrs.get('class', '')
    classes = f'{existing} {css_class}'.strip()
    return field.as_widget(attrs={'class': classes})
