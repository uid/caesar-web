#!/usr/bin/env python2.7
import sys, os, argparse, django, re, datetime, itertools, json
from pprint import pprint

# set up Django
sys.path.insert(0, "/var/django")
sys.path.insert(0, "/var/django/caesar")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caesar.settings")
django.setup()

from review.models import *
from get_milestone import get_milestone

parser = argparse.ArgumentParser(description="""
Make users into members of a class (as either students or staff).
Also creates user accounts for any who don't already have a Caesar account.
""")
parser.add_argument('--subject',
                    nargs=1,
                    type=str,
                    help="name of Subject; for example '6.005'")
parser.add_argument('--semester',
                    nargs=1,
                    type=str,
                    help="name of Semester; for example 'Fall 2013')")
parser.add_argument('--milestone',
                    metavar="ID",
                    type=int,
                    help="id number of SubmitMilestone; if omitted, uses the latest milestone whose deadline has passed.")


args = parser.parse_args()
#print args

milestone = get_milestone(args)
semester = milestone.assignment.semester
semester_name = semester.semester
subject_name = semester.subject.name

# convert e.g. Spring 2017 to sp17
m = re.match('(Fa|Sp)\w+ \d\d(\d\d)', semester_name)
if m == None:
    print("semester name doesn't follow Season Year format:", semester_name)
    exit(-1)
semester_abbr = m.group(1).lower() + m.group(2)

if args.milestone:
    milestone = SubmitMilestone.objects.get(id=args.milestone)
else:
    milestones = SubmitMilestone.objects.filter(\
        duedate__lte=datetime.datetime.now())\
        .order_by('-duedate')
    if len(milestones) == 0:
        print(subject, semester, "has no submit milestones that have passed")
        exit(-1)
    else:
        milestone = milestones[0]

pset = milestone.assignment.name # e.g. "ps0"
milestone_name = milestone.name # e.g. "beta"
print "updating snapshots for submit milestone #", milestone.id, pset, milestone_name


# in the code below,
# RevisionMap is a dictionary mapping
#   username:string -> revision:string, a revision hash in username's git repo for this pset


# deadline: datetime, max_extension: int, number of days of slack allowed on this deadline
# returns list of RevisionMaps of length max_extension+1, 
#    where sweeps[i] is the i-days-late RevisionMap, or None if no sweep found for that day
def find_sweeps(deadline, max_extension):
    sweeps_path = subject_name + "/didit/" + semester_abbr + "/sweeps/psets/" + pset
    sweep_filenames = os.listdir(sweeps_path)   

    # filename:string, sweeps folder name, assumed to have the form yymmddThhmmss, e.g. '20170122T221500'; 
    # returns int, number of days after deadline
    def days_after_deadline(filename):  
        return (datetime.datetime.strptime(filename, '%Y%m%dT%H%M%S') - deadline).days

    # choose the first sweep in each 1-day window
    # make sure we look at them in increasing chron order, since os.listdir() makes no order guarantee
    sweep_filenames.sort()
    sweep_filename_for_days_late = [None] * (max_extension + 1)
    for days_late, group in itertools.groupby(sweep_filenames, days_after_deadline):
        if days_late >= 0 and days_late <= max_extension:
            sweep_filename_for_days_late[days_late] = list(group)[0]

    # filename: string, sweeps foldername under sweeps_path
    # returns RevisionMap of that sweep
    def load_sweep(filename):
        with open(os.path.join(sweeps_path, filename, 'sweep.json'), 'r') as f:
            data = json.load(f)
            sweep = {}
            for entry in data['reporevs']:
                for user in entry['users']:
                    sweep[user] = entry['rev']
            return sweep
    return [load_sweep(filename) if filename else None for filename in sweep_filename_for_days_late]

# get the RevisionMap for each deadline
sweeps = find_sweeps(milestone.duedate, milestone.max_extension)
print "found sweeps for", [i for i in range(0,len(sweeps)) if sweeps[i]], "days late"
#pprint(sweeps)
# now sweep[n] is the RevisionMap for n days late (which may be None, if haven't done the n-day sweep yet)



# sweeps: list of max_extension+1 RevisionMaps, where sweeps[n] is the RevisionMap for n-days-late
# returns a new RevisionMap for every user whose deadline has passed, selecting the n-days-late revision
#     for that user if the user requested n days of slack
def select_revisions(sweeps):
    revisions_by_username = {}
    for username in set([username for sweep in sweeps if sweep for username in sweep.keys()]):
        sweep_to_use = 0 # assume no extension unless we discover otherwise
        try:
            user = Member.objects.get(semester=semester, user__username=username)
            try:
                extension = Extension.objects.get(user__username=username, milestone=milestone)
                sweep_to_use = extension.slack_used
            except Extension.DoesNotExist:
                pass # this is normal; users who didn't request slack have no Extension object
        except Member.DoesNotExist:
            print username, "found in sweep but not a member of the course in Caesar, assuming zero extension"
        if sweeps[sweep_to_use]:
            revisions_by_username[username] = sweeps[sweep_to_use][username]
    return revisions_by_username

revision_map = select_revisions(sweeps)
print "selected revisions for", len(revision_map), "users whose personal deadlines have passed"
#pprint(revision_map)


# revision_map: RevisionMap
# extracts a snapshot of each user's revision from their git repo (if that snapshot doesn't already exist),
# and makes a symlink to it in the right place 
def snapshot_revisions(revision_map):
    code_path = subject_name + "/private/" + semester_abbr + "/code/" + pset
    snapshots_path = os.path.join(code_path, "snapshots")
    links_path = os.path.join(code_path, milestone_name)
    staff_starting_path = os.path.join(code_path, 'staff')

    # make parent folders in case they don't exist yet
    [os.makedirs(path) for path in (snapshots_path, links_path, staff_starting_path) if not os.path.isdir(path)]

    # equivalent to ln -sf target source
    def symlink_force(target, source):
        os.remove(source) if os.path.exists(source) else None
        os.symlink(target, source)

    # make symlink to starting code in case it doesn't exist yet
    symlink_force('../../../staff/psets/' + pset + '/starting', os.path.join(staff_starting_path, 'starting'))

    for username in revision_map.keys():
        revision = revision_map[username]
        snapshot_name = username + "-" + revision
        print snapshot_name
        snapshot_path = os.path.join(code_path, "snapshots", snapshot_name)
        if not os.path.isdir(snapshot_path):
            os.makedirs(snapshot_path)
            command = 'git --git-dir="{subject}/git/{semester}/psets/{pset}/{username}.git" archive "{revision}" | tar x -C "{snapshot_folder}"'\
                        .format(subject=subject_name, semester=semester_abbr, pset=pset, username=username, revision=revision, snapshot_folder=snapshot_path)
            print command
            os.system(command)
        symlink_force("../snapshots/" + snapshot_name, os.path.join(links_path, username))

snapshot_revisions(revision_map)
