from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from memoria_quiz_app.models import CustomUser, Questions


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "password1", "password2",)


class UserSubjectsForm(ModelForm):
    class Meta :
        model = CustomUser
        fields = ("subject1", "difficulty_subject1", "subject2", "difficulty_subject2", "difficulty_general_culture")
        subject1 = forms.CharField(required=True, min_length=5)
        subject2 = forms.CharField(required=True, min_length=5)
        difficulty_subject1 = forms.ChoiceField(choices=CustomUser.difficulty_choices, required=True)
        difficulty_subject2 = forms.ChoiceField(choices=CustomUser.difficulty_choices, required=True)
        difficulty_general_culture = forms.ChoiceField(choices=CustomUser.difficulty_choices, required=True)
        widgets = {
            "subject1": forms.TextInput(attrs={"class": "form-control"}),
            "difficulty_subject1": forms.Select(attrs={"class": "form-control"}),
            "subject2": forms.TextInput(attrs={"class": "form-control"}),
            "difficulty_subject2": forms.Select(attrs={"class": "form-control"}),
            "difficulty_general_culture": forms.Select(attrs={"class": "form-control"}),
        }


class UserQuizForm(ModelForm):
    class Meta:
        model = Questions
        fields = ("user_answer", "is_answer_valid", "question_type",)
