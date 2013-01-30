from django import template

register = template.Library()

@register.filter(name='class_year')
def class_year(value):
  if value:
    return "'"+str(value)[2:]
  else:
    return ""
