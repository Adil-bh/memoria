from django.contrib.auth.forms import UserCreationForm

from memoria_quiz_app.models import CustomUser


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "first_name", "last_name", "password1", "password2",)
