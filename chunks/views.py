from chunks.models import Chunk, File
from comments.models import Comment, Vote, Star

from django.http import Http404
from django.shortcuts import render
from django.template import RequestContext
from django.contrib.auth.decorators import login_required


@login_required
def view_chunk(request, chunk_id):
    try:
        chunk = Chunk.objects.get(pk=chunk_id)

        def get_comment_data(comment):
            try:
                vote = comment.votes.get(author=request.user.id).value
            except Vote.DoesNotExist:
                vote = None
            snippet = chunk.generate_snippet(comment.start, comment.end)
            return (comment, vote, snippet)

        comment_data = map(get_comment_data,
                Comment.get_comments_for_chunk(chunk))
        
        #get the star data, or create it if it doesn't exist
        star = Star.objects.get_or_create(author=request.user,chunk=chunk)
    except Chunk.DoesNotExist:
        raise Http404
    return render(request, 'chunks/view_chunk.html', { 
        'chunk': chunk,
        'comment_data': comment_data,
        'star':star,
    }) 
