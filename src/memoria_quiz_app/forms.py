from django.contrib.auth.forms import UserCreationForm
from django.forms import EmailField

from memoria_quiz_app.models import CustomUser


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "password1", "password2",)