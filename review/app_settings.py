from django.conf import settings

CHUNKS_PER_REVIEWER = getattr(settings, 'REVIEW_CHUNKS_PER_REVIEWER', 3)
REVIEWERS_PER_CHUNK = getattr(settings, 'REVIEW_REVIEWERS_PER_CHUNK', 3)
