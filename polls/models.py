from django.contrib.auth.models import User
from django.db import models


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
class TopicRelation(models.Model):
    source = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="source_topic")
    target = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="target_topic")

    # Should these be backwards?
    class RelationType(models.IntegerChoices):
        CHILD_OF = 1
        PREREQ_OF = 2
    relation_type = models.IntegerField(choices=RelationType.choices)

    # Created by processing TopicRelationVotes.
    weight = models.FloatField(default=1)

    def __str__(self):
        return f"{self.source} -> {self.target}"


# should point to topicrelation? or no
class TopicRelationVote(models.Model):
    source = models.ForeignKey(Topic, on_delete=models.CASCADE)
    target = models.ForeignKey(Topic, on_delete=models.CASCADE)
    relation_type = models.IntegerField(choices=TopicRelation.RelationType.choices)

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


class Resource(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    link = models.CharField(max_length=200)
    # TODO: have comments purely for this resource? or only on ResourceRelation?

    def __str__(self):
        return self.title


class ResourceRelation(models.Model):
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    votes = models.IntegerField(default=0)
    # TODO: comments?

    def __str__(self):
        return f"({self.topic.title}) {self.resource.title}"
