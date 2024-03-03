from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Select

from memoria_quiz_app.models import CustomUser, Questions


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "password1", "password2",)


class UserSubjectsForm(ModelForm):
    class Meta :
        model = CustomUser
        fields = ("subject1", "difficulty_subject1", "subject2", "difficulty_subject2", "difficulty_general_culture")


class UserQuizForm(ModelForm):
    class Meta:
        model = Questions
        fields = ("user_answer_subject1", "user_answer_subject2", "user_answer_general_culture",
                  "is_answer_valid_subject1", "is_answer_valid_subject2", "is_answer_valid_general_culture")
