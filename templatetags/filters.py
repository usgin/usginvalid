from django.template.base import Library

register = Library()

def get(d, key):
    return d.get(key, '')

register.filter('get', get)