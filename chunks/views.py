from chunks.models import Chunk, File
from review.models import Comment, Vote, Star, Task

from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required


@login_required
def view_chunk(request, chunk_id):
    user = request.user
    chunk = get_object_or_404(Chunk, pk=chunk_id)
    def get_comment_data(comment):
        try:
            vote = comment.votes.get(author=user.id).value
        except Vote.DoesNotExist:
            vote = None
        snippet = chunk.generate_snippet(comment.start, comment.end)
        return (comment, vote, snippet)

    comment_data = map(get_comment_data,
            Comment.get_comments_for_chunk(chunk))
    
    #get the star data, or create it if it doesn't exist
    star = Star.objects.get_or_create(author=user,chunk=chunk)
    # get the associated task if it exists
    try:
        task = Task.objects.get(chunk=chunk, reviewer=user.get_profile())
    except Task.DoesNotExist:
        task = None
    return render(request, 'chunks/view_chunk.html', { 
        'chunk': chunk,
        'comment_data': comment_data,
        'star': star,
        'task': task,
    }) 