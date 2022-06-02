from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Topic, TopicRelationship

# Create your forms here.

class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title']


class TopicRelationshipForm(forms.ModelForm):
    class Meta:
        model = TopicRelationship
        fields = ['source', 'target', 'relation_type']

TopicRelationshipFormSet = forms.formset_factory(TopicRelationshipForm)
