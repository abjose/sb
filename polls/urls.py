from django.urls import path

from . import views

app_name = 'polls'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    # path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    # path('<int:question_id>/vote/', views.vote, name='vote'),

    path('topics/', views.TopicListView.as_view(), name='topics'),
    path('topics/search/', views.TopicSearchResultsView.as_view(), name='topic_search_results'),
    path('topics/<int:pk>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('topics/<int:topic_id>/known/', views.mark_known, name='mark_known'),
    path('topics/<int:topic_id>/goal/', views.mark_goal, name='mark_goal'),
    path('topics/<int:topic_id>/remove_goal/', views.remove_goal, name='remove_goal'),

    path('resources/<int:pk>/', views.ResourceDetailView.as_view(), name='resource_detail'),

    path('goals/<int:pk>/', views.GoalDetailView.as_view(), name='goal_detail'),

    # easy way to do username instead?
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),

    # probably should be in different app
    path("register", views.register_request, name="register")
]
