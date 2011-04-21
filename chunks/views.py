from caesar.chunks.models import Chunk, File

from django.http import Http404
from django.shortcuts import render_to_response
from django.template import RequestContext

import textwrap
import string

def view_chunk(request, chunk_id):
    try:
        chunk = Chunk.objects.get(pk=chunk_id)
        file_data = chunk.file.data
        # Rewind backwards from the offset to the beginning of the line
        first_line_offset = chunk.start
        while file_data[first_line_offset] != '\n':
            first_line_offset -= 1

        # TODO: make tab expansion configurable
        # TODO: more robust (custom) dedenting code
        data = file_data[first_line_offset + 1:chunk.end].expandtabs(4)
        data = textwrap.dedent(data)
    except Chunk.DoesNotExist:
        raise Http404
    return render_to_response('chunks/view_chunk.html', { 
        'chunk': chunk,
        'data': data
    }, context_instance=RequestContext(request)) 
