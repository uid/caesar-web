from django import template
from django.utils.translation import ugettext, ungettext
import datetime

register = template.Library()

@register.filter(name='timesince_human')
def humanize_timesince(date):
    delta = datetime.datetime.now() - date

    num_years = delta.days / 365
    if (num_years > 0):
        return ungettext(u"%d year", u"%d years", num_years) % num_years

    num_weeks = delta.days / 7
    if (num_weeks > 0):
        return ungettext(u"%d week", u"%d weeks", num_weeks) % num_weeks

    if (delta.days > 0):
        return ungettext(u"%d day", u"%d days", delta.days) % delta.days

    num_hours = delta.seconds / 3600
    if (num_hours > 0):
        return ungettext(u"%d hour", u"%d hours", num_hours) % num_hours

    num_minutes = delta.seconds / 60
    if (num_minutes > 0):
        return ungettext(u"%d minute", u"%d minutes", num_minutes) % num_minutes

    return ugettext(u"just a few seconds")
