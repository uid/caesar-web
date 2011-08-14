from __future__ import division

import random
import itertools
import operator
import math
import csv
import numpy
from collections import defaultdict

from chunks.models import Assignment
from tasks import app_settings
from tasks.routing import User, load_chunks, find_chunks


STAFF_PER_STUDENT = 0.05
OTHER_PER_STUDENT = 0.5
REPUTATION_SHAPE = 1.2 # justify this?
REPUTATION_STAFF_SHIFT = 20


def generate_users(student_count, reputation_alpha=REPUTATION_SHAPE):
    role_distribution = (
        ('student', student_count, 0),
        ('staff', int(student_count * STAFF_PER_STUDENT),
            REPUTATION_STAFF_SHIFT),
        ('other', int(student_count * OTHER_PER_STUDENT), 0),
    )

    users = []
    i = 1
    counts = dict((r, 0) for r in zip(*role_distribution)[0])
    for role, n, rep_shift in role_distribution:
        for _ in itertools.repeat(None, n):
            reputation = math.floor(random.paretovariate(reputation_alpha))
            reputation += rep_shift
            user = User(id=i, role=role, reputation=reputation)
            counts[role] += 1
            users.append(user)
            i += 1
    print "User statistics: "
    total = 0
    for role, count in counts.items():
        print "  %s: %d" % (role, count)
        total += count
    print "  total: %d" % total
    return users


def write_output(output_file, assignment, users, submissions):
    def write(*args):
        for s in args:
            output_file.write(str(s))
        output_file.write("\n")
    def write_header_line(s, level=1):
        write(('==' * level + ' ' + s + ' ').ljust(78, '='))
    write_header_line('Assignment: %s' % assignment.name)
    write()
    write_header_line('Chunk assignments', 2)
    write()
    students_with_staff = 0
    total = 0
    role_counts = {'student': 0, 'staff': 0, 'other': 0}
    for user in users:
        write_header_line(str(user), 3)
        staff_count = sum(r.role == 'staff' for r in user.other_reviewers)
        other_count = sum(r.role == 'other' for r in user.other_reviewers)
        write('Interactions:')
        write('  Staff: %d\n  Other: %d' % (staff_count, other_count))
        write()

        role_counts[user.role] += 1
        if user.role == 'student' and staff_count > 0:
            students_with_staff += 1
        for chunk in user.chunks:
            write('(Submission #%s) %s' % \
                    (chunk.submission.author.id, chunk.name))
            write('  Reviewers assigned to this chunk:')
            for reviewer in chunk.reviewers:
                write('    ', reviewer)
            write()

    write_header_line('Submissions', 2)
    write()
    submissions_with_staff = 0
    submissions_without_reviewers = 0
    minimum_reviewer_count = min(len(s.reviewers) for s in submissions)
    maximum_reviewer_count = max(len(s.reviewers) for s in submissions)
    chunk_reviewer_counts = defaultdict(lambda : 0)
    submission_stats = []
    for submission in submissions:
        for chunk in submission.chunks:
            chunk_reviewer_counts[len(chunk.reviewers)] += 1

        chunk_count = len(submission.chunks)
        reviewer_count = len(submission.reviewers)
        write_header_line('Submission #%d' % submission.author.id, 3)
        write('Chunks: %d' % chunk_count)
        chunks_with_reviewers = \
                sum(len(c.reviewers) > 0 for c in submission.chunks)
        if chunk_count == 0:
            coverage = 1
        else:
            coverage = chunks_with_reviewers / chunk_count
        
        write('Coverage: %f%%' % (100 * coverage))
        write()
        write('Reviewers:')
        for reviewer in submission.reviewers:
            write('  ', reviewer)

        submissions_with_staff += \
                any(r.role == 'staff' for r in submission.reviewers)
        if submission.chunks:
            submissions_without_reviewers += (len(submission.reviewers) == 0)

        submission_stats.append((chunk_count, chunks_with_reviewers, 
                                 reviewer_count, coverage))
        write()

    min_stats = numpy.amin(submission_stats, axis=0)
    max_stats = numpy.amax(submission_stats, axis=0)
    avg_stats = numpy.mean(submission_stats, axis=0)
    std_stats = numpy.std(submission_stats, axis=0)

    write_header_line('Summary statistics', 2)
    write('Population:')
    for role, count in role_counts.items():
        write("  %s: %d" % (role.capitalize(), count))
        total += count
    write("  Total: %d" % total)
    write()
    write('  Students with staff on chunk: %d' % students_with_staff)
    write()
    write('Submissions:')
    write('  Total: %d' % len(submissions))
    write('  Without reviewers: %d' % submissions_without_reviewers)
    write('  With staff reviewers: %d' % submissions_with_staff)
    write('  Reviewer count:')
    write('    Min: %f' % min_stats[2])
    write('    Max: %f' % max_stats[2])
    write('    Avg: %f' % avg_stats[2])
    write('    Std: %f' % std_stats[2])
    write('  Coverage:')
    write('    Min: %f%%' % (100 * min_stats[3]))
    write('    Max: %f%%' % (100 * max_stats[3]))
    write('    Avg: %f%%' % (100 * avg_stats[3]))
    write('    Std: %f%%' % (100 * std_stats[3]))
    write()
    write('Chunks')
    for n, count in sorted(chunk_reviewer_counts.items()):
        write('  %d reviewers: %d' % (n, count))
    write()  
    write()


def write_data(output_file, assignment, users, submissions):
    writer = csv.writer(output_file)
    for user in users:
        writer.writerow([user.id, user.role, user.reputation])

    writer.writerow([])
    for submission in submissions:
        for chunk in submission.chunks:
            writer.writerow([chunk.name, len(chunk.reviewers)])


def run():
    with open('task_sim_output.txt', 'w') as f, \
            open('task_sim_data.csv', 'w') as f_data:
        for assignment in Assignment.objects.all():
            print "Running assignment for assignment: %s" % assignment.name

            submission_count = assignment.submissions.count()
            student_count = submission_count
            if assignment.name in ("6.005/multipart", "6.005/antibattleship"):
               student_count *= 3 
            users = generate_users(student_count)
            user_map = defaultdict(lambda : None)
            for user in users:
                user_map[user.id] = user
            chunks = load_chunks(assignment, user_map)
            print "%d chunks loaded" % (len(chunks),)

            submissions = {}
            for chunk in chunks:
                submissions[chunk.submission.id] = chunk.submission
            
            # simulate random arrival order of users
            random.shuffle(users)
            users.sort(key=lambda u: u.role == 'staff')

            # connect fake users to submissions
            submission_queue = submissions.values()
            for user in users:
                if user.role == 'student':
                    submission = submission_queue.pop()
                    submission.author = user
                    if not submission_queue:
                        break

            for user in users:
                assign_count = app_settings.CHUNKS_PER_ROLE[user.role]
                list(find_chunks(user, chunks, assign_count))

            write_output(f, assignment, users, submissions.viewvalues())
            write_data(f_data, assignment, users, submissions.viewvalues())
            print 
    
