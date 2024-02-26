from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm, Select

from memoria_quiz_app.models import CustomUser


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "password1", "password2",)


class UserSubjectsForm(ModelForm):
    class Meta :
        model = CustomUser
        fields = ("subject1", "difficulty_subject1", "subject2", "difficulty_subject2", "difficulty_general_culture")