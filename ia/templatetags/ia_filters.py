from django import template

register = template.Library()


@register.filter
def lookup(dictionary, key):
    """Template filter para acceder a diccionarios con claves dinámicas"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''


@register.filter
def replace_underscores(value):
    """Reemplaza guiones bajos con espacios"""
    if not value:
        return value
    return str(value).replace('_', ' ')
