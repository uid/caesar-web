from chunks.models import Chunk, File
from comments.models import Comment, Vote, Star

from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

import textwrap
import string

@login_required
def view_chunk(request, chunk_id):
    try:
        chunk = Chunk.objects.get(pk=chunk_id)
        file_data = chunk.file.data
        # Rewind backwards from the offset to the beginning of the line
        first_line_offset = chunk.start
        while file_data[first_line_offset] != '\n':
            first_line_offset -= 1
        first_line_offset += 1

        first_line = file_data.count("\n", 0, first_line_offset)+1

        # TODO: make tab expansion configurable
        # TODO: more robust (custom) dedenting code
        data = file_data[first_line_offset:chunk.end].expandtabs(4)
        lines = list(enumerate(textwrap.dedent(data).splitlines(), 
            start=first_line))

        def get_comment_data(comment):
            try:
                vote = comment.votes.get(author=request.user.id).value
            except Vote.DoesNotExist:
                vote = None
            snippet = lines[comment.start - first_line][1]
            return (comment, vote, snippet)

        comment_data = map(get_comment_data, Comment.get_comments_for_chunk(chunk))
        
        #get the star data, or create it if it doesn't exist
        star = Star.objects.get_or_create(author=request.user,chunk=chunk)
    except Chunk.DoesNotExist:
        raise Http404
    return render_to_response('chunks/view_chunk.html', { 
        'chunk': chunk,
        'lines': lines,
        'comment_data': comment_data,
        'star':star,
    }, context_instance=RequestContext(request)) 
