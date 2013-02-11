from django import template

register = template.Library()

@register.filter
def is_enrolled(semester, enrolled_classes):
	enrolled = False
	if enrolled_classes.filter(semester=semester):
		enrolled = True
	return enrolled