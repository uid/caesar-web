from django.conf import settings

CHUNKS_PER_ROLE = getattr(settings, 'TASKS_CHUNKS_PER_ROLE', {
    'student': 8,
    'staff': 28,
    'other': 5,
})

REVIEWERS_PER_CHUNK = getattr(settings, 'TASKS_REVIEWERS_PER_CHUNK', 2)

ROLE_AFFINITY_MULTIPLIER = getattr(settings, 'TASKS_ROLE_AFFINITY_MULTIPLIER',
                                   100)
