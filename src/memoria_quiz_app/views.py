import ast
import datetime
import json
import os

import openai
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponseRedirect, HttpResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView, CreateView, ListView
from dotenv import load_dotenv

from memoria_quiz_app.forms import UserRegistrationForm, UserSubjectsForm, UserQuizForm
from .models import CustomUser, Questions
from .quiz import generate_questions, check_answer_and_scoring, user_can_play, reset_win_streak, \
    return_subject_quiz_page, \
    format_answer_options, reset_is_answered_question_bool, select_difficulty, user_has_question, \
    return_subject_question_type, question_creation, return_subject_quiz_url
from .tokens import account_activation_token

load_dotenv()
api_key = os.getenv("OPEN_AI_KEY")
openai.api_key = api_key


# User account creation
def activate(request, uidb64, token):
    '''
    Function that activates user account when email link has been clicked on. Then redirects the user on an
    other page.
    '''
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Merci d'avoir confirmé votre email. Vous pouvez maintenant vous connecter. ")
        return redirect("memoria:login")
    else:
        messages.error(request, "Lien d'activation invalide.")
    return redirect('memoria:home')


def activateEmail(request, user, to_email):
    '''
    Function that send confirmation email to user.
    '''
    mail_subject = _("Activez votre compte")
    message = render_to_string("activate_account/template_activate_account.html", {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to=[to_email])
    if email.send():
        messages.success(request, f"Cher {user}, veuillez vérifier votre adresse email {to_email}")
    else:
        messages.error(request, f"Problem sending email to {to_email}, check if you typed it correctly.")


def signup(request):
    context = {}
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect("memoria:home")
        else:
            context["form"] = form
    else:
        form = UserRegistrationForm()
        context["form"] = form

    return render(request, "memoria/signup.html", context)


# Subject choice, edit and stats
class SubjectChoice(ListView):
    model = CustomUser
    questions = Questions
    template_name = "subjects/subject_index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = CustomUser.objects.get(pk=self.request.user.id)
        context["questions"] = Questions.objects.filter(user=context["user"]).first()
        return context


class SubjectEdit(UpdateView):
    model = CustomUser
    questions = Questions
    template_name = "subjects/subject_edit.html"
    fields = ["subject1", "difficulty_subject1", "subject2", "difficulty_subject2", "difficulty_general_culture", ]

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        current_user = request.user.id
        user_to_edit = CustomUser.objects.get(pk=self.kwargs['pk']).pk
        if current_user == user_to_edit:
            self.object = self.get_object()
            return super().get(request, *args, **kwargs)
        else:
            messages.error(request, "Erreur")
            return redirect("memoria:index-subjects")

    def post(self, request, *args, **kwargs):
        form = UserSubjectsForm(request.POST)
        user_to_edit = CustomUser.objects.get(pk=self.kwargs['pk'])
        if form.is_valid():
            old_subject1 = user_to_edit.subject1
            old_difficulty_subject1 = user_to_edit.difficulty_subject1
            old_subject2 = user_to_edit.subject2
            old_difficulty_subject2 = user_to_edit.difficulty_subject2
            old_difficulty_general_culture = user_to_edit.difficulty_general_culture
            user_to_edit.subject1 = form.cleaned_data['subject1']
            user_to_edit.subject2 = form.cleaned_data['subject2']
            user_to_edit.difficulty_subject1 = form.cleaned_data['difficulty_subject1']
            user_to_edit.difficulty_subject2 = form.cleaned_data['difficulty_subject2']
            user_to_edit.difficulty_general_culture = form.cleaned_data['difficulty_general_culture']
            reset_win_streak(user_to_edit, "subject1", user_to_edit.subject1, old_subject1)
            reset_win_streak(user_to_edit, "subject2", user_to_edit.subject2, old_subject2)
            user_to_edit.save()

            # Generate new questions if the subject has changed
            if old_subject1 != user_to_edit.subject1 or user_to_edit.subject1 is None or Questions.objects.filter(
                    is_question_answered=1,
                    user=user_to_edit).count() >= 20 or old_difficulty_subject1 != user_to_edit.difficulty_subject1:
                Questions.objects.filter(subject="subject1", user=user_to_edit).delete()
                try:
                    response_data = json.loads(
                    generate_questions(user_to_edit, "subject1", user_to_edit.difficulty_subject1))
                except Exception as e:
                    print(f"Error: {e}")
                    messages.error(request, "Erreur lors de la génération des questions.")
                    return redirect("memoria:index-subjects")
                questions_subject1 = response_data['questions']
                for question_json in questions_subject1:
                    question = question_json['question']
                    question_type = question_json['type']
                    expected_answer = question_json['answer']
                    options = question_json.get('options')
                    try:
                        explication = question_json['explanation']
                    except:
                        explication = None
                    question_creation(user_to_edit, "subject1", question, question_type, options, explication,
                                      expected_answer)

            # Generate new questions if the subject has changed
            if old_subject2 != user_to_edit.subject2 or user_to_edit.subject2 is None or Questions.objects.filter(
                    is_question_answered=1,
                    user=user_to_edit).count() >= 20 or old_difficulty_subject2 != user_to_edit.difficulty_subject2:
                Questions.objects.filter(subject="subject2", user=user_to_edit).delete()
                try:
                    response_data = json.loads(
                    generate_questions(user_to_edit, "subject2", user_to_edit.difficulty_subject2))
                except Exception as e:
                    print(f"Error: {e}")
                    messages.error(request, "Erreur lors de la génération des questions.")
                    return redirect("memoria:index-subjects")
                questions_subject2 = response_data['questions']
                for question_json in questions_subject2:
                    question = question_json['question']
                    question_type = question_json['type']
                    expected_answer = question_json['answer']
                    options = question_json.get('options')
                    try:
                        explication = question_json['explanation']
                    except:
                        explication = None
                    question_creation(user_to_edit, "subject2", question, question_type, options, explication,
                                      expected_answer)

            # Generate new questions if the there is no question in the database
            # or if the user has answered 20 questions
            if (not Questions.objects.filter(subject="general_culture",
                                            user=user_to_edit).exists() or
                    Questions.objects.filter(is_question_answered=1, user=user_to_edit).count() >= 20 or
                    old_difficulty_general_culture != user_to_edit.difficulty_general_culture):
                try:
                    response_data = json.loads(generate_questions(user_to_edit,
                                                             "general_culture",
                                                              user_to_edit.difficulty_general_culture))
                except Exception as e:
                    print(f"Error: {e}")
                    messages.error(request, "Erreur lors de la génération des questions.")
                    return redirect("memoria:index-subjects")
                questions_general_culture = response_data['questions']
                for question_json in questions_general_culture:
                    # print(question_json)
                    question = question_json['question']
                    question_type = question_json['type']
                    expected_answer = question_json['answer']
                    options = question_json.get('options')
                    try:
                        explication = question_json['explanation']
                    except:
                        explication = None
                    question_creation(user_to_edit, "general_culture", question, question_type, options, explication,
                                      expected_answer)

            messages.success(request, "Les changements ont été pris en compte !")
            return redirect("memoria:index-subjects")
        else:
            form = UserSubjectsForm()
            return render(request, "memoria/subject_edit.html", context={"form": form})


# Quizz creation with OpenAI API
class QuizView(CreateView):
    model = Questions
    user = CustomUser
    template_name = "quiz_page/quiz_page.html"
    fields = "__all__"

    def get(self, request, *args, **kwargs):
        context = {}
        form = UserQuizForm()
        context["form"] = form

        # Récupérer l'utilisateur actuel, le sujet
        user_to_ask = get_object_or_404(CustomUser, id=request.user.id)
        url_subject = self.kwargs['subject']

        # Vérifier si l'utilisateur a entré ses thèmes avant de jouer
        if user_to_ask.subject1 is None or user_to_ask.subject2 is None:
            messages.error(request, "Veuillez définir vos thèmes dans la section avant de jouer.")
            return redirect("memoria:index-subjects")

        # Vérifier si l'utilisateur a déjà répondu à une question sur le sujet 1 aujourd'hui
        if user_can_play(url_subject, "subject1", user_to_ask.date_last_question_subject1):
            question = Questions.objects.filter(user=user_to_ask,
                                                subject="subject1",
                                                is_question_answered=False).first()
            reset_is_answered_question_bool(url_subject, question)
            question.date_answered = datetime.datetime.today()  # On attribue la date du jour à la question
            question.save()
            context["question"] = question
            context['options'] = ast.literal_eval(question.options)
            return render(request, "quiz_page/quiz_subject1_page.html", context)

        # Vérifier si l'utilisateur a déjà répondu à une question sur le sujet 2 aujourd'hui
        elif user_can_play(url_subject, "subject2", user_to_ask.date_last_question_subject2):
            question = Questions.objects.filter(user=user_to_ask,
                                                subject="subject2",
                                                is_question_answered=False).first()
            reset_is_answered_question_bool(url_subject, question)
            question.date_answered = datetime.datetime.now()  # On attribue la date du jour à la question
            question.save()
            context["question"] = question
            context['options'] = ast.literal_eval(question.options)
            return render(request, "quiz_page/quiz_subject2_page.html", context)

        # Vérifier si l'utilisateur a déjà répondu à une question sur la culture générale aujourd'hui
        elif user_can_play(url_subject, "general_culture", user_to_ask.date_last_question_general_culture):
            question = Questions.objects.filter(user=user_to_ask,
                                                subject="general_culture",
                                                is_question_answered=False).first()
            reset_is_answered_question_bool(url_subject, question)
            question.date_answered = datetime.datetime.now()  # On attribue la date du jour à la question
            question.save()
            context["question"] = question
            context['options'] = ast.literal_eval(question.options)
            return render(request, "quiz_page/quiz_general_culture_page.html", context)
        else:
            # Sinon on lui affiche les questions auxquelles il a déjà répondu
            context['user'] = user_to_ask
            context['question'] = Questions.objects.get(user=user_to_ask, subject=url_subject,
                                                        date_answered=datetime.date.today())
            context['options'] = ast.literal_eval(context['question'].options)
            page = return_subject_quiz_page(url_subject)
            return render(request, f"{page}", context)

    def post(self, request, *args, **kwargs):

        # Récupérer l'utilisateur actuel, le sujet et la question du jour
        context = {"subject": self.kwargs['subject']}
        form = UserQuizForm(request.POST)
        user = get_object_or_404(CustomUser, id=request.user.id)
        question = get_object_or_404(Questions, user=user, subject=self.kwargs['subject'],
                                     date_answered=datetime.date.today())  # On récupère la question du jour avec la date du jour

        # Vérifier si la réponse de l'utilisateur est correcte, et mettre à jour les scores
        if form.is_valid():
            print(form.cleaned_data)
            if self.kwargs['subject'] == "subject1":
                user_answer = form.cleaned_data['user_answer']
                question_type = form.cleaned_data['question_type']
                question.user_answer = user_answer
                check_answer_and_scoring(user, question, "subject1", question_type)
                user.date_last_question_subject1 = datetime.date.today()
                question.is_question_answered = True  # Set question as answered
                user.save()
                question.save()
            elif self.kwargs['subject'] == "subject2":
                user_answer = form.cleaned_data['user_answer']
                question_type = form.cleaned_data['question_type']
                question.user_answer = user_answer
                check_answer_and_scoring(user, question, "subject2", question_type)
                user.date_last_question_subject2 = datetime.date.today()
                question.is_question_answered = True
                user.save()
                question.save()
            else:
                user_answer = form.cleaned_data['user_answer']
                question_type = form.cleaned_data['question_type']
                question.user_answer = user_answer
                check_answer_and_scoring(user, question, "general_culture", question_type)
                user.date_last_question_general_culture = datetime.date.today()
                question.is_question_answered = True
                user.save()
                question.save()
            answer = form.cleaned_data
            print(answer)
        else:

            context['form_errors'] = form.errors
            context["user"] = user
            context["question"] = question
            context["form"] = form

        context['form_errors'] = form.errors
        context["user"] = user
        context["question"] = question
        context["form"] = form

        # Renvoyer la page de quiz avec la réponse correcte
        url = return_subject_quiz_url(self.kwargs['subject'])
        return HttpResponseRedirect(f'{url}', context)


# Homepage
def home(request):
    return render(request, "memoria/home.html")


# Static pages
def about(request):
    return render(request, "about.html")


def privacy(request):
    return render(request, "privacy.html")


def legals(request):
    return render(request, "legals.html")
