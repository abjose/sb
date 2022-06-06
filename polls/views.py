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

from random import choice

from .forms import TopicForm, TopicRelationFormSet
from .models import Topic, TopicRelation, Resource, UserGoal, UserKnowledge


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    model = Topic  # TODO: get rid of this

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        context['random_topic'] = choice(Topic.objects.all())

        return context


class TopicListView(generic.ListView):
    model = Topic
    paginate_by = 30
    ordering = ["title"]


class TopicDetailView(generic.DetailView):
    model = Topic

    def get_context_data(self, **kwargs):
        context = super(TopicDetailView, self).get_context_data(**kwargs)

        context['resource_list'] = Resource.objects.filter(topic=self.object.id)

        context['prereq_list'] = TopicRelation.objects.filter(
            target=self.object.id
        ).filter(
            relation_type=TopicRelation.RelationType.PREREQ_OF
        )
        context['succ_list'] = TopicRelation.objects.filter(
            source=self.object.id
        ).filter(
            relation_type=TopicRelation.RelationType.PREREQ_OF
        )

        context['parent_list'] = TopicRelation.objects.filter(
            source=self.object.id
        ).filter(
            relation_type=TopicRelation.RelationType.CHILD_OF
        )
        context['child_list'] = TopicRelation.objects.filter(
            target=self.object.id
        ).filter(
            relation_type=TopicRelation.RelationType.CHILD_OF
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


# require login?
class UserDetailView(generic.DetailView):
    model = User
    template_name = 'polls/user_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UserDetailView, self).get_context_data(**kwargs)

        context['goals'] = UserGoal.objects.filter(user=self.object.id)
        context['known'] = UserKnowledge.objects.filter(user=self.object.id)

        context['next_steps'] = dict()
        for goal in context['goals']:
            goal_topic_id = goal.topic.id
            context['next_steps'][goal.topic.title] = get_next_steps(goal_topic_id, self.object.id)

        return context


@login_required
def mark_known(request, topic_id):
    # MAKE A NEW TopicRelation
    # then redirect to... user page? or back to topic
    # TODO: should use AJAX probably
    # print(f"topic id: {topic_id}")
    # print(f"user id: {request.user.id}")

    existing = UserKnowledge.objects.filter(
        user=request.user.id
    ).filter(
        topic=topic_id
    )

    if len(existing) == 0:
        print("Topic not yet marked as known; adding.")
        topic = get_object_or_404(Topic, pk=topic_id)
        known = UserKnowledge(
            user=request.user,
            topic=topic)
        known.save()

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
    existing = UserGoal.objects.filter(
        user=request.user.id
    ).filter(
        topic=topic_id
    )

    if len(existing) == 0:
        topic = get_object_or_404(Topic, pk=topic_id)
        goal = UserGoal(
            user=request.user,
            topic=topic)
        goal.save()

    return HttpResponseRedirect(reverse('polls:topic_detail', args=[topic_id]))


@login_required
def remove_goal(request, topic_id):
    existing = UserGoal.objects.filter(
        user=request.user.id
    ).filter(
        target=topic_id
    )

    if len(existing) > 0:
        existing[0].delete()

    return HttpResponseRedirect(reverse('polls:user_detail', args=[request.user.id]))


@login_required
def vote_for_resource(request, resource_id):
    res = Resource.objects.get(pk=resource_id)
    res.votes += 1
    res.save()
    return HttpResponseRedirect(reverse('polls:topic_detail', args=[res.topic.id]))


# Return a list of all prereq topics for the given topic.
def get_all_prereqs(topic_id, user_id):
    # TODO: use a graph db or in-memory graph or anything other than this.
    prereq_topics = set()  # WARNING - uses id to hash, so if not saved won't work.
    next_steps = set()  # Only the "boundary" of unknown topics.
    open_set = set([Topic.objects.get(pk=topic_id)])
    closed_set = set()  # seem there are some cycles somewhere?

    known_topics = set()
    if user_id:
        known = UserKnowledge.objects.filter(user=user_id)
        known_topics = set([k.topic for k in known])
        print("known topics: ", known_topics)

    while len(open_set) > 0:
        curr_topic = open_set.pop()
        if curr_topic in closed_set:
            continue
        closed_set.add(curr_topic)

        prereq_relations = TopicRelation.objects.filter(target=curr_topic).filter(
            relation_type=TopicRelation.RelationType.PREREQ_OF
        )
        added_child = False
        for rel in prereq_relations:
            if rel.source in known_topics:
                print(f"already know {rel.source.title}")
                continue
            print(f"adding {rel.source.title}")
            open_set.add(rel.source)
            prereq_topics.add(rel.source)
            added_child = True

        # Add children topics too.
        child_relations = TopicRelation.objects.filter(target=curr_topic).filter(
            relation_type=TopicRelation.RelationType.CHILD_OF
        )
        for rel in child_relations:
            if rel.source in known_topics:
                print(f"already know {rel.source.title}")
                continue
            print(f"adding {rel.source.title}")
            open_set.add(rel.source)
            prereq_topics.add(rel.source)
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


def edit_topic(request, topic_id=None):
    topic = Topic.objects.get(pk=topic_id)

    relationships = list(TopicRelation.objects.filter(source=topic_id).values())
    relationships.extend(TopicRelation.objects.filter(target=topic_id).values())

    for rel in relationships:
        # can just get if don't do values()?
        source = Topic.objects.get(pk=rel['source_id'])
        target = Topic.objects.get(pk=rel['target_id'])
        rel['source'] = source
        rel['target'] = target

    print(f"found {len(relationships)} rels")
    print(relationships)

    rel_forms = TopicRelationFormSet(initial=relationships)
    # print(rel_forms.as_table())

    # if not request.user:
    #     form = ChoiceResponseForm()
    #     return render(request, 'polls/question_detail.html', {'object': question, 'form': form})

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        # form = ChoiceResponseForm(request.POST, instance=choice)  # will this overwrite new values?
        # # check whether it's valid:
        # if form.is_valid():
        #     # process the data in form.cleaned_data as required
        #     form.save()
        #     return HttpResponseRedirect('/polls/questions/')
        pass

    # if a GET (or any other method) we'll create a blank form
    else:
        form = TopicForm(instance=topic)

    return render(request, 'polls/edit_topic.html', {'object': topic, 'form': form, 'rel_forms': rel_forms})
