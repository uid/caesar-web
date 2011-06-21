from chunks.models import Chunk
from review.models import Comment

def run():
    total_deleted = 0
    for chunk in Chunk.objects.all():
        if chunk.id % 2 == 0:
            chunk_comments = chunk.comments.filter(type='S')
            count = chunk_comments.count()
            print "%d comments deleted for chunk %d" % \
                    (chunk_comments.count(), chunk.id)
            chunk.comments.filter(type='S').delete()
            total_deleted += count
    print "\n%d comments deleted in total" % total_deleted
