from caesar.chunks.models import Chunk, File

from django.http import Http404
from django.shortcuts import render_to_response

def view_chunk(request, chunk_id):
    try:
        chunk = Chunk.objects.get(pk=chunk_id)
    except Chunk.DoesNotExist:
        raise Http404
    return render_to_response('chunks/chunk.html', { 'chunk': chunk }) 
