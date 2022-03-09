from django.contrib import admin

from .models import Topic, Relationship, Resource


class RelationshipAdmin(admin.ModelAdmin):
    list_filter = ['relation_type']
    search_fields = ['source_topic__title', 'target_topic__title', 'user__username']

admin.site.register(Relationship, RelationshipAdmin)


admin.site.register(Topic)
admin.site.register(Resource)
# admin.site.register(Relationship)
