import datetime

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

    @admin.display(
        boolean=True,
        ordering='pub_date',
        description='Published recently?',
    )
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text


class Topic(models.Model):
    title = models.CharField(max_length=200)

    # How does this compare to having explicit Edges?
    # parent_topics = models.ManyToManyField(
    #     to='self', symmetrical=False, blank=True)
    # prereq_topics = models.ManyToManyField(
    #     to='self', blank=True)
    # https://stackoverflow.com/questions/46268059/django-many-to-many-recursive-relationship

    # resources = models.ManyToManyField(Resource)
    # ehh, maybe just keep as foreign key - otherwise hard to keep track of topic-specific date for a resource

    def __str__(self):
        return self.title


# TODO: investigate performance of this vs. ManyToMany version.
class TopicRelationship(models.Model):
    source = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="source_topic")
    target = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="target_topic")

    # Should these be backwards?
    class RelationType(models.IntegerChoices):
        CHILD_OF = 1
        PREREQ_OF = 2
    relation_type = models.IntegerField(choices=RelationType.choices)

    # Created by processing TopicRelVotes.
    weight = models.FloatField(default=1)

    def __str__(self):
        return f"{self.source} -> {self.target}"


# should point to topicrel? or no
class TopicRelVote(models.Model):
    source = models.ForeignKey(Topic, on_delete=models.CASCADE)
    target = models.ForeignKey(Topic, on_delete=models.CASCADE)
    relation_type = models.IntegerField(choices=TopicRelationship.RelationType.choices)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.CharField(max_length=200)
    reason = models.TextField()

    # some possible vote sources
    # - user votes
    # - references to textbooks / trustworthy sources
    # - also optionally a text description of why

    def __str__(self):
        return f"vote for {self.source} -> {self.target}"


class UserGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} has goal of {self.topic}"


class UserKnowledge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} knows {self.target}"


# Want to be able to reference many topics?
# Use Relationship instead?
class Resource(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    link = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.title


# Do you need explicit goals? goals are just topics, right? could be collections of topics, but then that should be its own topic, probably
# class Goal(models.Model):
#     topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
#     resource_title = models.CharField(max_length=200)
#     resource_link = models.CharField(max_length=200)

#     def __str__(self):
#         return self.resource_title
