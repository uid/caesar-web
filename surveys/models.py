from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

# Create your models here.

class Corpus(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created = models.TimeField(auto_now_add=True)
    owner = models.ForeignKey(User, related_name='corpora')
    
    class Meta:
        unique_together = (('owner', 'name'))

class Chunk(models.Model):
    corpus = models.ForeignKey(Corpus, related_name='chunks')
    body = models.TextField()

class Survey(models.Model):
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, related_name='surveys')
    corpus = models.ForeignKey(Corpus, related_name='surveys')
    class Meta:
        unique_together = (('owner', 'name'))

TASK_TYPE_CHOICES = (
    ('T', 'Text Input'),
    ('A', 'Text Area'),
) 

class Task(models.Model):
    survey = models.ForeignKey(Survey, related_name='tasks')
    prompt = models.TextField()
    task_type = models.CharField(max_length=2, choices=TASK_TYPE_CHOICES)


