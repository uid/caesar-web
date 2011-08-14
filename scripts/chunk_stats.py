import numpy

from chunks.models import Assignment, Chunk

def run():
    for assignment in Assignment.objects.all():
        chunks = Chunk.objects.find_by_assignment(assignment) \
                .select_related('file')
        sizes = [c.lines[-1][0] - c.lines[0][0] for c in chunks]
        print assignment.name
        print "min: %d, max: %d, avg: %f, std: %f" % (
                numpy.min(sizes),
                numpy.max(sizes),
                numpy.mean(sizes),
                numpy.std(sizes)
        )

