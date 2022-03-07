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
    ordering = ["title"]


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
        print(f"Getting prereqs for user {self.request.user.id}")
        context['prereqs'], _ = get_all_prereqs(self.object.id, self.request.user.id)
        print(f"Done getting prereqs, found {len(context['prereqs'])}")
        return context


class ResourceDetailView(generic.DetailView):
    model = Resource


class TopicSearchResultsView(generic.ListView):
    model = Topic
    template_name = 'polls/topic_search_results.html'
    paginate_by = 30
    ordering = ["title"]

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = Topic.objects.filter(
            Q(title__icontains=query) # | Q(state__icontains=query)
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

        context['goals'] = Relationship.objects.filter(
            user=self.object.id
        ).filter(
            relation_type=Relationship.RelationType.GOAL_OF
        )

        context['next_steps'] = dict()
        for goal_rel in context['goals']:
            goal_topic_id = goal_rel.target_topic.id
            context['next_steps'][goal_rel.target_topic.title] = get_next_steps(goal_topic_id, self.object.id)

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


@login_required
def mark_goal(request, topic_id):
    existing_rel = Relationship.objects.filter(
        user=request.user.id
    ).filter(
        target_topic=topic_id
    ).filter(
        relation_type=Relationship.RelationType.GOAL_OF
    )

    if len(existing_rel) == 0:
        topic = get_object_or_404(Topic, pk=topic_id)
        rel = Relationship(
            user=request.user,
            target_topic=topic,
            relation_type=Relationship.RelationType.GOAL_OF)
        rel.save()

    return HttpResponseRedirect(reverse('polls:topic_detail', args=[topic_id]))


@login_required
def remove_goal(request, topic_id):
    existing_rel = Relationship.objects.filter(
        user=request.user.id
    ).filter(
        target_topic=topic_id
    ).filter(
        relation_type=Relationship.RelationType.GOAL_OF
    )

    if len(existing_rel) > 0:
        existing_rel[0].delete()

    return HttpResponseRedirect(reverse('polls:user_detail', args=[request.user.id]))


# Return a list of all prereq topics for the given topic.
def get_all_prereqs(topic_id, user_id):
    # TODO: use a graph db or in-memory graph or anything other than this.
    prereq_topics = set()  # WARNING - uses id to hash, so if not saved won't work.
    next_steps = set()  # Only the "boundary" of unknown topics.
    open_set = set([Topic.objects.get(pk=topic_id)])
    closed_set = set()  # seem there are some cycles somewhere?

    known_topics = set()
    if user_id:
        known_rels = Relationship.objects.filter(user=user_id).filter(
            relation_type=Relationship.RelationType.KNOWLEDGE_OF
        )
        known_topics = set([rel.target_topic for rel in known_rels])
        print("known topics: ", known_topics)

    while len(open_set) > 0:
        curr_topic = open_set.pop()
        if curr_topic in closed_set:
            continue
        closed_set.add(curr_topic)

        prereq_relations = Relationship.objects.filter(target_topic=curr_topic).filter(
            relation_type=Relationship.RelationType.PREREQ_OF
        )
        added_child = False
        for rel in prereq_relations:
            if rel.source_topic in known_topics:
                print(f"already know {rel.source_topic.title}")
                continue
            print(f"adding {rel.source_topic.title}")
            open_set.add(rel.source_topic)
            prereq_topics.add(rel.source_topic)
            added_child = True

        # Add children topics too.
        child_relations = Relationship.objects.filter(target_topic=curr_topic).filter(
            relation_type=Relationship.RelationType.CHILD_OF
        )
        for rel in child_relations:
            if rel.source_topic in known_topics:
                print(f"already know {rel.source_topic.title}")
                continue
            print(f"adding {rel.source_topic.title}")
            open_set.add(rel.source_topic)
            prereq_topics.add(rel.source_topic)
            added_child = True

        if not added_child and curr_topic not in known_topics:
            # Add (unknown) nodes with no unknown children/predecessors.
            print(f"marking {curr_topic.title} as a next_step")
            next_steps.add(curr_topic)

    # TODO: make sure ordered?
    return prereq_topics, next_steps


def get_next_steps(topic_id, user_id):
    # TODO: change prereqs function to return something more like a graph instead?
    _, next_steps = get_all_prereqs(topic_id, user_id)
    return next_steps


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
