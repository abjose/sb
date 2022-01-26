from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

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
    paginate_by = 30
    model = Topic
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


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'


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
