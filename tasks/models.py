# from datetime import datetime
# from django.db import models
# from django.contrib.auth.models import User
# from chunks.models import Chunk, ReviewMilestone, Submission

# class ChunkReview(models.Model):
#     chunk = models.OneToOneField(Chunk, related_name='chunk_review', null=True, blank=True)
#     id = models.AutoField(primary_key=True)
#     # student_reviewers = models.IntegerField(default=0)
#     # alum_reviewers = models.IntegerField(default=0)
#     student_or_alum_reviewers = models.IntegerField(default=0)
#     staff_reviewers = models.IntegerField(default=0)
#     # reviewer_ids = models.TextField(blank=True) #space separated list of chunk names [name checked, ]

#     # def reset(self):
#     #     self.student_or_alum_reviewers = 0
#     #     self.staff_reviewers = 0

#     # def add_reviewer_id(self,id):
#     #     self.reviewer_ids += ' ' + str(id)

#     # def remove_reviewer_id(self,id):
#     #     self.reviewer_ids = self.reviewer_ids.replace(' '+str(id),'')

#     # def reviewer_ids(self):
#     #     return list(map(int,self.reviewer_ids.split()))

#     def __unicode__(self):
#         return u'chunk_review - %s' % (self.id)

# class Task(models.Model):
#     STATUS_CHOICES=(
#         ('N', 'New'),
#         ('O', 'Opened'),
#         ('S', 'Started'),
#         ('C', 'Completed'),
#         ('U', 'Unfinished'),
#     )
    
#     submission = models.ForeignKey(Submission, related_name='tasks', null=True, blank=True)
#     chunk = models.ForeignKey(Chunk, related_name='tasks', null=True, blank=True)
#     chunk_review = models.ForeignKey(ChunkReview, related_name='tasks', null=True, blank=True)
#     reviewer = models.ForeignKey(User, related_name='tasks', null=True)
#     milestone = models.ForeignKey(ReviewMilestone, related_name='tasks')
#     status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='N')
#     # TODO switch to a more robust model history tracking (e.g. versioning)
#     created = models.DateTimeField(auto_now_add=True)
#     opened = models.DateTimeField(blank=True, null=True)
#     started = models.DateTimeField(blank=True, null=True)
#     completed = models.DateTimeField(blank=True, null=True)

#     # how should tasks be sorted in the dashboard?
#     def sort_key(self):
#         try:
#             return int(self.submission.name)
#         except:
#             return self.submission.name

#     class Meta:
#         unique_together = ('chunk', 'reviewer',)

#     def __unicode__(self):
#         return "Task: %s - %s" % (self.reviewer, self.chunk)

#     def mark_as(self, status):
#         if status not in zip(*Task.STATUS_CHOICES)[0]:
#             raise Exception('Invalid task status')

#         self.status = status
#         if status == 'N':
#             self.opened = None
#             self.started = None
#             self.completed = None
#         elif status == 'O':
#             self.opened = datetime.now()
#         elif status == 'S':
#             self.started = datetime.now()
#         elif status == 'C':
#             self.completed = datetime.now()

#         self.save()

#     def name(self):
#         return self.chunk.name if self.chunk != None else self.submission.name
    
#     def authors(self):
#       return self.submission.authors

