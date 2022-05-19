from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Topic, Relationship

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


class RelationshipForm(forms.ModelForm):
    class Meta:
        model = Relationship
        fields = ['source_topic', 'target_topic', 'relation_type']

RelationshipFormSet = forms.formset_factory(RelationshipForm)
