from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    difficulty_choices = (
        ("EASY", "Facile"),
        ("MEDIUM", "Moyen"),
        ("HARD", "Difficile"),
        ("EXPERT", "Expert")

    )

    win_streak = models.PositiveIntegerField(blank=True, auto_created=True, default=0)
    date_last_question = models.ForeignKey("Question", on_delete=models.SET_NULL, null=True)

    subject1 = models.CharField(blank=True, max_length=255)
    subject2 = models.CharField(blank=True, null=True, max_length=255)
    difficulty_subject1 = models.CharField(difficulty_choices, choices=difficulty_choices, max_length=50)
    difficulty_subject2 = models.CharField(difficulty_choices, choices=difficulty_choices, max_length=50)
    difficulty_general_culture = models.CharField(difficulty_choices, choices=difficulty_choices, max_length=50)

    number_answered_questions_s1 = models.PositiveIntegerField(blank=True, default=0)
    number_answered_questions_s2 = models.PositiveIntegerField(blank=True, default=0)
    number_answered_questions_general_culture = models.PositiveIntegerField(blank=True, default=0)
    total_answered_questions = models.PositiveIntegerField(blank=True, default=0)

    number_valid_answers_s1 = models.PositiveIntegerField(blank=True, default=0)
    number_valid_answers_s2 = models.PositiveIntegerField(blank=True, default=0)
    number_valid_answers_general_culture = models.PositiveIntegerField(blank=True, default=0)
    total_valid_answers = models.PositiveIntegerField(blank=True, default=0)

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


class Question(models.Model):
    question_type = (
        ("QCM", "QCM"),
        ("Open_question", "Question ouverte")
    )
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE, null=True, blank=True)
    question = models.TextField(blank=True, null=False)
    date_last_question = models.DateField(auto_now=True)
    question_type = models.CharField(question_type, choices=question_type, max_length=20)
    expected_answer = models.TextField(blank=True)


class Answer(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.SET_NULL, null=True)
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)
    user_answer = models.TextField(blank=True)
    is_answer_correct = models.BooleanField(default=False)