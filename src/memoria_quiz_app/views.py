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
from .quiz import quiz_generator, check_answer_and_scoring, can_user_play, reset_win_streak, return_subject_quiz_page, \
    format_answer_options, reset_is_answered_question_bool, select_difficulty
from .tokens import account_activation_token

load_dotenv()


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

    if User is not None and account_activation_token.check_token(user, token):
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
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect("memoria:home")
    else:
        form = UserRegistrationForm()

    return render(request, "memoria/signup.html", context={"form": form})


# Subject choice, edit and stats
class SubjectChoice(ListView):
    model = CustomUser
    questions = Questions
    template_name = "subjects/subject_index.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = CustomUser.objects.get(pk=self.request.user.id)
        context["questions"] = Questions.objects.get(user=context["user"])
        return context


class SubjectEdit(UpdateView):
    model = CustomUser
    template_name = "subjects/subject_edit.html"
    fields = ["subject1", "difficulty_subject1", "subject2", "difficulty_subject2", "difficulty_general_culture", ]

    def get(self, request, *args, **kwargs):
        current_user = request.user.id
        user_to_edit = CustomUser.objects.get(pk=self.kwargs['pk']).pk
        if current_user == user_to_edit:
            self.object = self.get_object()
            return super().get(request, *args, **kwargs)
        else:
            messages.error(request, "Accès refusé")
            return redirect("memoria:index-subjects")

    def post(self, request, *args, **kwargs):
        form = UserSubjectsForm(request.POST)
        user_to_edit = CustomUser.objects.get(pk=self.kwargs['pk'])
        if form.is_valid():
            old_subject1 = user_to_edit.subject1
            old_subject2 = user_to_edit.subject2
            user_to_edit.subject1 = form.cleaned_data['subject1']
            user_to_edit.subject2 = form.cleaned_data['subject2']
            user_to_edit.difficulty_subject1 = form.cleaned_data['difficulty_subject1']
            user_to_edit.difficulty_subject2 = form.cleaned_data['difficulty_subject2']
            user_to_edit.difficulty_general_culture = form.cleaned_data['difficulty_general_culture']
            reset_win_streak(user_to_edit, "subject1", user_to_edit.subject1, old_subject1)
            reset_win_streak(user_to_edit, "subject2", user_to_edit.subject2, old_subject2)
            user_to_edit.save()
            messages.success(request, "Les changements ont été pris en compte !")
            return redirect("memoria:index-subjects")
        else:
            form = UserSubjectsForm()
            return render(request, "memoria/subject_edit.html", context={"form": form})


def subject_statistics(request):
    pass


# Quizz creation with OpenAI API
class QuizGenerator(CreateView):
    model = Questions
    user = CustomUser
    template_name = "quiz_page/quiz_page.html"
    fields = "__all__"
    api_key = os.getenv("OPEN_AI_KEY")
    openai.api_key = api_key

    def get(self, request, *args, **kwargs):
        context = {}
        form = UserQuizForm()
        context["form"] = form

        # Récupérer l'utilisateur actuel, le sujet et la difficulté
        user_to_ask = get_object_or_404(CustomUser, id=request.user.id)
        url_subject = self.kwargs['subject']
        difficulty = select_difficulty(user_to_ask, url_subject)
        question = Questions.objects.get(user=user_to_ask)

        # Générer une question avec l'API OpenAI, si l'utilisateur peut jouer
        if can_user_play(url_subject, "subject1", user_to_ask.date_last_question_subject1):
            reset_is_answered_question_bool(url_subject, question)
            response = quiz_generator(user_to_ask, url_subject, difficulty, question.question_subject1)
        elif can_user_play(url_subject, "subject2", user_to_ask.date_last_question_subject2):
            reset_is_answered_question_bool(url_subject, question)
            response = quiz_generator(user_to_ask, url_subject, difficulty, question.question_subject2)
        elif can_user_play(url_subject, "general_culture", user_to_ask.date_last_question_general_culture):
            reset_is_answered_question_bool(url_subject, question)
            response = quiz_generator(user_to_ask, url_subject, difficulty, question.question_general_culture)
        else:
            context['user'] = user_to_ask
            context['question'] = Questions.objects.get(user=user_to_ask)
            page = return_subject_quiz_page(url_subject)
            context['options'] = format_answer_options(url_subject, context)
            return render(request, f"{page}", context)

        # Récupérer la question, le type de question, la réponse attendue et les options
        json_response = json.loads(response)
        print(json.dumps(json_response, indent=4, ensure_ascii=False))

        question = json_response['question']
        question_type = json_response['type']
        expected_answer = json_response['answer']
        options = json_response.get('options')

        # Vérifier si l'utilisateur a déjà une question dans notre base de données
        # Pour remplacer la question existante par la nouvelle question
        has_question = Questions.objects.filter(user=user_to_ask).exists()
        print(has_question)

        # Si l'utilisateur a déjà une question, on la met à jour, sinon on la crée
        if has_question:
            if url_subject == "subject1":
                Questions.objects.filter(user=user_to_ask).update(
                    user=user_to_ask,
                    question_subject1=question,
                    question_type_subject1=1 if question_type == "QCM" else 0,
                    expected_answer_subject1=expected_answer,
                    options_subject1=options if question_type == "QCM" else None
                )
                updated_question = Questions.objects.get(user=user_to_ask)

                context["question"] = updated_question
                context["question"].options_subject1 = ast.literal_eval(context["question"].options_subject1)
                context["subject"] = url_subject
                return render(request, "quiz_page/quiz_subject1_page.html", context)
            elif url_subject == "subject2":
                Questions.objects.filter(user=user_to_ask).update(
                    user=user_to_ask,
                    question_subject2=question,
                    question_type_subject2=1 if question_type == "QCM" else 0,
                    expected_answer_subject2=expected_answer,
                    options_subject2=options if question_type == "QCM" else None
                )
                updated_question = Questions.objects.get(user=user_to_ask)

                context["question"] = updated_question
                context["question"].options_subject2 = ast.literal_eval(context["question"].options_subject2)
                context["subject"] = url_subject
                return render(request, "quiz_page/quiz_subject2_page.html", context)
            else:
                Questions.objects.filter(user=user_to_ask).update(
                    user=user_to_ask,
                    question_general_culture=question,
                    question_type_general_culture=1 if question_type == "QCM" else 0,
                    expected_answer_general_culture=expected_answer,
                    options_general_culture=options if question_type == "QCM" else None
                )
                updated_question = Questions.objects.get(user=user_to_ask)
                context["question"] = updated_question
                context["question"].options_general_culture = ast.literal_eval(context["question"].options_general_culture)
                context["subject"] = url_subject
                return render(request, "quiz_page/quiz_general_culture_page.html", context)
        else:
            if url_subject == "subject1":
                question_obj = Questions(user=user_to_ask,
                                         question_subject1=question,
                                         question_type_subject1=1 if question_type == "QCM" else 0,
                                         expected_answer_subject1=expected_answer,
                                         options_subject1=options if question_type == "QCM" else None)
                question_obj.save()
                context["question"] = question_obj
                context["subject"] = url_subject
                return render(request, "quiz_page/quiz_subject1_page.html", context)
            elif url_subject == "subject2":
                question_obj = Questions(user=user_to_ask,
                                         question_subject2=question,
                                         question_type_subject2=1 if question_type == "QCM" else 0,
                                         expected_answer_subject2=expected_answer,
                                         options_subject2=options if question_type == "QCM" else None)
                question_obj.save()
                context["question"] = question_obj
                context["subject"] = url_subject
                return render(request, "quiz_page/quiz_subject2_page.html", context)
            else:
                question_obj = Questions(user=user_to_ask,
                                         question_general_culture=question,
                                         question_type_general_culture=1 if question_type == "QCM" else 0,
                                         expected_answer_general_culture=expected_answer,
                                         options_general_culture=options if question_type == "QCM" else None)
                question_obj.save()
                context["question"] = question_obj
                context["subject"] = url_subject
                return render(request, "quiz_page/quiz_general_culture_page.html", context)

    def post(self, request, *args, **kwargs):
        # Récupérer l'utilisateur actuel, le sujet et la difficulté
        context = {"subject": self.kwargs['subject']}
        form = UserQuizForm(request.POST)
        user = get_object_or_404(CustomUser, id=request.user.id)
        question = get_object_or_404(Questions, user=user)

        # Vérifier si la réponse de l'utilisateur est correcte, et mettre à jour les scores
        if form.is_valid():
            if self.kwargs['subject'] == "subject1":
                user_answer = form.cleaned_data['user_answer_subject1']
                question.user_answer_subject1 = user_answer
                check_answer_and_scoring(user, question, "subject1")
                user.date_last_question_subject1 = datetime.date.today()
                question.is_question_answered_subject1 = True    # Set question as answered
                user.save()
                question.save()
            elif self.kwargs['subject'] == "subject2":
                user_answer = form.cleaned_data['user_answer_subject2']
                question.user_answer_subject2 = user_answer
                check_answer_and_scoring(user, question, "subject2")
                user.date_last_question_subject2 = datetime.date.today()
                question.is_question_answered_subject2 = True
                user.save()
                question.save()
            else:
                user_answer = form.cleaned_data['user_answer_general_culture']
                question.user_answer_general_culture = user_answer
                check_answer_and_scoring(user, question, "general_culture")
                user.date_last_question_general_culture = datetime.date.today()
                question.is_question_answered_general_culture = True
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
        page_to_return = return_subject_quiz_page(self.kwargs['subject'])
        return render(request, f"{page_to_return}", context)


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
