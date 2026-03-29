from django import template

register = template.Library()


@register.filter(name='add_class', is_safe=True)
def add_class(field, css_class):
    """Add CSS classes to a form field widget."""
    existing = field.field.widget.attrs.get('class', '')
    classes = f'{existing} {css_class}'.strip()
    return field.as_widget(attrs={'class': classes})
