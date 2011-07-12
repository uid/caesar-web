from __future__ import division
from chunks.models import *
from review.models import *


def run():
    total_comment_counts = []
    pruned_comment_counts = []
    unpruned_comment_counts = []
    blank_comment_counts = []

    chunks = {}
    for task in Task.objects.exclude(status='N'):
        chunks[task.chunk_id] = task.chunk

    for id, chunk in chunks.items():
        user_comment_count = chunk.comments.filter(type='U').count()
        static_comment_count = chunk.comments.filter(type='S').count()
        comment_counts = (user_comment_count, static_comment_count)
        total_comment_counts.append(comment_counts)

        if chunk.id % 2 == 0: # deleted Checkstyle comments
            pruned_comment_counts.append(comment_counts)
        else:
            unpruned_comment_counts.append(comment_counts)

        if static_comment_count == 0:
            blank_comment_counts.append(comment_counts)

    def print_stats(counts):
        user_counts, static_counts = zip(*counts)
        n = len(counts)
        print "Average user comment count: ", sum(user_counts) / n

    print (" ALL CHUNKS (%d) " % len(total_comment_counts)).center(79, '=')
    print_stats(total_comment_counts)

    print (" UNPRUNED CHUNKS (%d) " % len(unpruned_comment_counts)).center(79, '=')
    print_stats(unpruned_comment_counts)

    print (" PRUNED CHUNKS (%d) " % len(pruned_comment_counts)).center(79, '=')
    print_stats(pruned_comment_counts)

    print (" BLANK CHUNKS (%d) " % len(blank_comment_counts)).center(79, '=')
    print_stats(blank_comment_counts)





