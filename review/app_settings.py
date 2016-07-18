from django.conf import settings

# this is never used
# CHUNKS_PER_ROLE = getattr(settings, 'TASKS_CHUNKS_PER_ROLE', {
#     'student': 5,
#     'staff': 10,
#     'other': 5,
# })

REVIEWERS_PER_CHUNK = getattr(settings, 'TASKS_REVIEWERS_PER_CHUNK', 2)

ROLE_AFFINITY_MULTIPLIER = getattr(settings, 'TASKS_ROLE_AFFINITY_MULTIPLIER',
                                   100)

CHUNKS_PER_CLUSTER = getattr(settings, 'TASKS_CHUNKS_PER_CLUSTER', 3)

CHUNK_SIMILARITY_THRESHOLD = getattr(
        settings, 'CHUNKS_CHUNK_SIMILARITY_THRESHOLD', .4)

SIMILAR_CHUNK_LIMIT = getattr(
        settings, 'CHUNKS_SIMILAR_CHUNK_LIMIT', 10)
