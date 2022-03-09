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
class Relationship(models.Model):
    source_topic = models.ForeignKey(Topic, related_name="successor_relations", null=True, on_delete=models.CASCADE)
    target_topic = models.ForeignKey(Topic, related_name="predecessor_relations", on_delete=models.CASCADE)

    # If this is a 'knowledge' or 'goal' relation (i.e. user U knows/has goal of topic T) then uses
    # this field and `target_topic`.
    # TODO: Could atlernatively have a UserKnowledge model or something.
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    # Should these be backwards?
    class RelationType(models.IntegerChoices):
        CHILD_OF = 1
        PREREQ_OF = 2
        KNOWLEDGE_OF = 3
        GOAL_OF = 4
    relation_type = models.IntegerField(choices=RelationType.choices)

    # one big advantage of explicit Relationship model - can easily have stuff like weights!
    weight = models.FloatField(default=1)

    def __str__(self):
        if self.user:
            if self.relation_type == Relationship.RelationType.KNOWLEDGE_OF:
                return f"{self.user} knows {self.target_topic}"
            else:
                return f"{self.user} has goal of {self.target_topic}"
        return f"{self.source_topic} -> {self.target_topic}"


# Want to be able to reference many topics?
# Use Relationship instead?
class Resource(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    link = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.resource_title


# Do you need explicit goals? goals are just topics, right? could be collections of topics, but then that should be its own topic, probably
# class Goal(models.Model):
#     topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
#     resource_title = models.CharField(max_length=200)
#     resource_link = models.CharField(max_length=200)

#     def __str__(self):
#         return self.resource_title
