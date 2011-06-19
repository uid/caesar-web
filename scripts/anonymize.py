import re

from chunks.models import Chunk

def run():
    names = set()
    with open('data/names.txt', 'r') as f:
        for line in f:
            for name in re.split('\s+', line.lower()):
                if name: names.add(name)

    for chunk in Chunk.objects.all():
        for n, line in chunk.lines:
            if any((w in names) for w in re.split('\s+', line)):
                print "%d: %s" % (chunk.id, line)
                

