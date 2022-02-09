from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .models import Choice, Question, Topic, Relationship, Resource


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')[:5]


class TopicListView(generic.ListView):
    model = Topic
    paginate_by = 30
    ordering = ["topic_title"]


class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class TopicDetailView(generic.DetailView):
    model = Topic

    def get_context_data(self, **kwargs):
        context = super(TopicDetailView, self).get_context_data(**kwargs)

        context['resource_list'] = Resource.objects.filter(topic=self.object.id)

        context['prereq_list'] = Relationship.objects.filter(
            target_topic=self.object.id
        ).filter(
            relation_type=Relationship.RelationType.PREREQ_OF
        )
        context['succ_list'] = Relationship.objects.filter(
            source_topic=self.object.id
        ).filter(
            relation_type=Relationship.RelationType.PREREQ_OF
        )

        context['parent_list'] = Relationship.objects.filter(
            source_topic=self.object.id
        ).filter(
            relation_type=Relationship.RelationType.CHILD_OF
        )
        context['child_list'] = Relationship.objects.filter(
            target_topic=self.object.id
        ).filter(
            relation_type=Relationship.RelationType.CHILD_OF
        )

        return context


class GoalDetailView(generic.DetailView):
    model = Topic
    template_name = 'polls/goal_detail.html'

    def get_context_data(self, **kwargs):
        context = super(GoalDetailView, self).get_context_data(**kwargs)
        print("Getting prereqs")
        context['prereqs'] = get_all_prereqs(self.object.id)
        print(f"Done getting prereqs, found {len(context['prereqs'])}")
        return context


class ResourceDetailView(generic.DetailView):
    model = Resource


class TopicSearchResultsView(generic.ListView):
    model = Topic
    template_name = 'polls/topic_search_results.html'
    paginate_by = 30
    ordering = ["topic_title"]

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = Topic.objects.filter(
            Q(topic_title__icontains=query) # | Q(state__icontains=query)
        )
        return object_list


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'


# require login?
class UserDetailView(generic.DetailView):
    model = User
    template_name = 'polls/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)

        context['known'] = Relationship.objects.filter(
            user=self.object.id
        ).filter(
            relation_type=Relationship.RelationType.KNOWLEDGE_OF
        )

        return context


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


@login_required
def mark_known(request, topic_id):
    # MAKE A NEW Relationship
    # then redirect to... user page? or back to topic
    # TODO: should use AJAX probably
    # print(f"topic id: {topic_id}")
    # print(f"user id: {request.user.id}")

    existing_rel = Relationship.objects.filter(
        user=request.user.id
    ).filter(
        target_topic=topic_id
    ).filter(
        relation_type=Relationship.RelationType.KNOWLEDGE_OF
    )

    if len(existing_rel) == 0:
        print("Topic not yet marked as known; adding.")
        topic = get_object_or_404(Topic, pk=topic_id)
        rel = Relationship(
            user=request.user,
            target_topic=topic,
            relation_type=Relationship.RelationType.KNOWLEDGE_OF)
        rel.save()

    # return HttpResponseRedirect(reverse('polls:user_detail', args=[request.user.id]))
    return HttpResponseRedirect(reverse('polls:topic_detail', args=[topic_id]))

    # try:
    #     selected_choice = question.choice_set.get(pk=request.POST['choice'])
    # except (KeyError, Choice.DoesNotExist):
    #     # Redisplay the question voting form.
    #     return render(request, 'polls/detail.html', {
    #         'question': question,
    #         'error_message': "You didn't select a choice.",
    #     })
    # else:
    #     selected_choice.votes += 1
    #     selected_choice.save()
    #     # Always return an HttpResponseRedirect after successfully dealing
    #     # with POST data. This prevents data from being posted twice if a
    #     # user hits the Back button.
    #     return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
    # redirect to user page instead?


# Return a list of all prereq topics for the given topic.
def get_all_prereqs(topic_id):
    # TODO: use a graph db or in-memory graph or anything other than this.
    prereq_topics = set()  # what will it use to hash?
    open_set = set([topic_id])
    while (len(open_set) > 0):
        curr_id = open_set.pop()
        prereq_relations = Relationship.objects.filter(target_topic=curr_id).filter(
            relation_type=Relationship.RelationType.PREREQ_OF
        )
        for rel in prereq_relations:
            print(f"adding {rel.source_topic.topic_title}")
            open_set.add(rel.source_topic.id)
            prereq_topics.add(rel.source_topic)

    # TODO: make sure ordered?
    return prereq_topics


# Probably should be in a different app
def register_request(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            print("Registration successful!")
            # messages.success(request, "Registration successful." )
            # return redirect("main:homepage")
            return redirect("polls:topics")
        print("Unsuccessful registration")
        # messages.error(request, "Unsuccessful registration. Invalid information.")
    form = UserCreationForm()
    return render (request=request, template_name="polls/register.html", context={"register_form":form})
