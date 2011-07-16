from django.conf import settings

CHUNK_SIMILARITY_THRESHOLD = getattr(
        settings, 'CHUNKS_CHUNK_SIMILARITY_THRESHOLD', .4)

SIMILAR_CHUNK_LIMIT = getattr(
        settings, 'CHUNKS_SIMILAR_CHUNK_LIMIT', 10)
