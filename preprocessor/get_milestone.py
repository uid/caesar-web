from review.models import *

# args: command-line args returned by ArgumentParser.parse_args.  Assumes has subject, semester, and milestone arguments,
#   as used by preprocess.py and takeSnapshots.py.
# returns SubmitMilestone object or throws error
def get_milestone(args):
    if args.milestone:
        return SubmitMilestone.objects.get(id=args.milestone)
    else:
        if not args.subject or not args.semester:
            raise Exception("need to specify either --subject --semester, or --milestone.  See --help for details.")
        milestones = SubmitMilestone.objects.filter(\
            assignment__semester__subject__name=args.subject[0],
            assignment__semester__semester=args.semester[0],
            duedate__lte=datetime.datetime.now())\
            .order_by('-duedate')
        if len(milestones) == 0:
            raise Exception(subject + " " + semester + " has no submit milestones that have passed")
        return milestones[0]
