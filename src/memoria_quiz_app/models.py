from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinLengthValidator
from django.urls import reverse
from django.utils import timezone, dateformat

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):

    def create_user(self, username, first_name, last_name, email, password):
        if not email:
            raise ValueError("Vous devez entrer une adresse email.")
        email = self.normalize_email(email)
        user = self.model(username=username, first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, email, password, first_name, last_name):
        user = self.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
        user.is_staff = True
        user.is_admin = True
        user.is_superuser = True
        user.save()
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):
    difficulty_choices = (
        (None, "Choisissez une difficulté"),
        ("EASY", "Facile"),
        ("MEDIUM", "Moyen"),
        ("HARD", "Difficile"),
        ("EXPERT", "Expert")
    )

    username_validator = UnicodeUsernameValidator()
    username = models.CharField(_("username"), max_length=15, unique=True, blank=False,
                                validators=[username_validator, MinLengthValidator(4)],
                                error_messages={
                                    "unique": "Nom d'utilisateur déjà utilisé",
                                })
    first_name = models.CharField(_("first name"), max_length=60, blank=False, )
    last_name = models.CharField(_("last name"), max_length=60, blank=False)
    email = models.EmailField(max_length=255, blank=False, unique=True)
    is_active = models.BooleanField(default=False, help_text="Designates whether this user should be treated as active.")
    is_staff = models.BooleanField(default=False,
                                   help_text="Designates whether the user can log into this admin site.")
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]
    objects = CustomUserManager()

    win_streak_subject1 = models.PositiveIntegerField(blank=True, auto_created=True, default=0)
    win_streak_subject2 = models.PositiveIntegerField(blank=True, auto_created=True, default=0)
    win_streak_general_culture = models.PositiveIntegerField(blank=True, auto_created=True, default=0)
    date_last_question_subject1 = models.DateField(blank=True, null=True)
    date_last_question_subject2 = models.DateField(blank=True, null=True)
    date_last_question_general_culture = models.DateField(blank=True, null=True)

    subject1 = models.CharField(_("Thème 1"), blank=False, null=True, max_length=255)
    subject2 = models.CharField(_("Thème 2"), blank=False, null=True, max_length=255)
    difficulty_subject1 = models.CharField(_("Difficulté Thème 1"), choices=difficulty_choices, max_length=50)
    difficulty_subject2 = models.CharField(_("Difficulté Thème 2"), choices=difficulty_choices, max_length=50)
    difficulty_general_culture = models.CharField(_("Difficulté Culture générale"), choices=difficulty_choices,
                                                  max_length=50)

    number_answered_questions_s1 = models.PositiveIntegerField(blank=True, default=0)
    number_answered_questions_s2 = models.PositiveIntegerField(blank=True, default=0)
    number_answered_questions_general_culture = models.PositiveIntegerField(blank=True, default=0)

    number_valid_answers_s1 = models.PositiveIntegerField(blank=True, default=0)
    number_valid_answers_s2 = models.PositiveIntegerField(blank=True, default=0)
    number_valid_answers_general_culture = models.PositiveIntegerField(blank=True, default=0)

    emoji_subject1 = models.CharField(blank=True, max_length=100)
    emoji_subject2 = models.CharField(blank=True, max_length=100)

    class Meta:
        verbose_name = "User"

    @property
    def win_rate(self):
        try:
            return f"{(self.total_valid_answers / self.total_answered_questions) * 100} %"
        except ZeroDivisionError:
            return None

    @property
    def total_answered_questions(self):
        return self.number_answered_questions_s1 + self.number_answered_questions_s2 + self.number_answered_questions_general_culture

    @property
    def total_valid_answers(self):
        return self.number_valid_answers_s1 + self.number_valid_answers_s2 + self.number_valid_answers_general_culture

    def get_absolute_url(self):
        return reverse('memoria:home')


class Questions(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE, null=True)

    question = models.TextField(blank=True, null=False, help_text="Question")
    subject = models.CharField(max_length=255, blank=True, null=True, help_text="Sujet de la question")
    options = models.CharField(max_length=500, blank=True, null=True, help_text="Options de  réponse pour la question")
    question_type = models.BooleanField(default=True, help_text="True if question is a multiple choice question")
    expected_answer = models.TextField(blank=True, null=True, help_text="Réponse attendue")
    explication_answer = models.TextField(blank=True, null=True, help_text="Explication de la réponse")
    user_answer = models.TextField(blank=True, verbose_name="Réponse de l'utilisateur")
    is_answer_valid = models.BooleanField(default=False, help_text="True if user's answer is valid")
    is_question_answered = models.BooleanField(default=False, help_text="True if user has answered the question")
    date_answered = models.DateField(default=None, blank=True, null=True, help_text="Date when the question was answered")