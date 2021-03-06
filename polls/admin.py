from django.contrib import admin

from .models import Topic, TopicRelation, TopicRelationVote, Resource, ResourceRelation, UserGoal, UserKnowledge


class TopicRelationAdmin(admin.ModelAdmin):
    list_filter = ['relation_type']
    search_fields = ['source__title', 'target__title']


admin.site.register(Topic)
admin.site.register(TopicRelation, TopicRelationAdmin)
admin.site.register(TopicRelationVote)
admin.site.register(Resource)
admin.site.register(ResourceRelation)
admin.site.register(UserGoal)
admin.site.register(UserKnowledge)
