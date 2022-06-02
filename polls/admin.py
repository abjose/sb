from django.contrib import admin

from .models import Topic, TopicRelationship, TopicRelVote, Resource


class TopicRelationshipAdmin(admin.ModelAdmin):
    list_filter = ['relation_type']
    search_fields = ['source__title', 'target__title']

admin.site.register(TopicRelationship, TopicRelationshipAdmin)


admin.site.register(Topic)
admin.site.register(Resource)
admin.site.register(TopicRelVote)
