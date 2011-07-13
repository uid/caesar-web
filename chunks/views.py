from chunks.models import Chunk, File, Assignment
from review.models import Comment, Vote, Star 
from tasks.models import Task

from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from pygments import highlight
from pygments.lexers import JavaLexer
from pygments.formatters import HtmlFormatter

@login_required
def view_chunk(request, chunk_id):
    user = request.user
    chunk = get_object_or_404(Chunk, pk=chunk_id)
    user_votes = dict((vote.comment_id, vote.value) \
            for vote in user.votes.filter(comment__chunk=chunk_id))

    def get_comment_data(comment):
        vote = user_votes.get(comment.id, None)
        snippet = chunk.generate_snippet(comment.start, comment.end)
        return (comment, vote, snippet)

    comment_data = map(get_comment_data,
            Comment.get_comments_for_chunk(chunk))

    lexer = JavaLexer()
    formatter = HtmlFormatter(cssclass='syntax', nowrap=True)
    numbers, lines = zip(*chunk.lines)
    # highlight the code this way to correctly identify multi-line constructs
    # TODO implement a custom formatter to do this instead
    highlighted_lines = zip(numbers, 
            highlight(chunk.data, lexer, formatter).splitlines())
    
    task_count = Task.objects.filter(reviewer=user.get_profile()) \
            .exclude(status='C').count()
    # get the associated task if it exists
    try:
        task = Task.objects.get(chunk=chunk, reviewer=user.get_profile())
        if task.status == 'N':
            task.mark_as('O')
    except Task.DoesNotExist:
        task = None
    return render(request, 'chunks/view_chunk.html', { 
        'chunk': chunk,
        'highlighted_lines': highlighted_lines,
        'comment_data': comment_data,
        'task': task,
        'task_count': task_count
    }) 
def view_all_chunks(request, assign, username):
    chunks = Chunk.objects.filter(file__submission__name=username).filter(file__submission__assignment__name=assign)
    
    return render(request, 'chunks/view_all_chunks.html', {
        'chunks': chunks
    })
