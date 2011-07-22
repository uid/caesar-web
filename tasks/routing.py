from django.db.models import Count

from chunks.models import Chunk
from models import Task
import app_settings

def find_chunks(assignment, user):
    """
    Retrieves the chunks for this user to review on this assignment.

    Does not assign them, this method simply retrieves chunk instances.
    """
    reviewer = user.get_profile()
    current_task_count = Task.objects.filter(reviewer=reviewer, 
            chunk__file__submission__assignment=assignment).count()
    
    assign_count = app_settings.CHUNKS_PER_REVIEWER - current_task_count
    if assign_count <= 0:
        return None

    # Retrieve all remotely possible chunks
    chunks = Chunk.objects.exclude(file__submission__author=user) \
            .filter(file__submission__assignment=assignment) \
            .exclude(tasks__reviewer=reviewer) 

    # Annotate the chunks with counts
    chunks = chunks.annotate(
            reviewer_count=Count('tasks'),
            submission_reviewer_count=Count(
                'file__submission__files__chunks__tasks'))

    # FIXME this query will probably need to be optimized
    chunks = chunks \
            .filter(reviewer_count__lt=app_settings.REVIEWERS_PER_CHUNK) \
            .order_by('-reviewer_count')[0:assign_count]

    return chunks


def assign_tasks(assignment, user):
    """
    Assigns chunks to the user for review, if the user does not have enough.

    Returns the number of chunks assigned.
    """
    chunks = find_chunks(assignment, user)
    if not chunks:
        return 0
    
    assign_count = 0
    for chunk in chunks:
        task = Task(reviewer=user.get_profile(), chunk=chunk)
        task.save()
        assign_count += 1
        
    return assign_count


