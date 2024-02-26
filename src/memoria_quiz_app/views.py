from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from memoria_quiz_app.forms import UserRegistrationForm, UserSubjectsForm
from .models import CustomUser
from .tokens import account_activation_token


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
def subject_choice(request):
    return render(request, "subjects/subject_index.html")


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
            messages.error(request,"Accès refusé")
            return redirect("memoria:index-subjects")

    def post(self, request, *args, **kwargs):
        form = UserSubjectsForm(request.POST)
        user_to_edit = CustomUser.objects.get(pk=self.kwargs['pk'])
        if form.is_valid():
            user_to_edit.subject1 = form.cleaned_data['subject1']
            user_to_edit.subject2 = form.cleaned_data['subject2']
            user_to_edit.difficulty_subject1 = form.cleaned_data['difficulty_subject1']
            user_to_edit.difficulty_subject2 = form.cleaned_data['difficulty_subject2']
            user_to_edit.difficulty_general_culture = form.cleaned_data['difficulty_general_culture']
            user_to_edit.save()
            messages.success(request, "Les changements ont été pris en compte !")
            return redirect("memoria:index-subjects")
        else:
            form = UserSubjectsForm()
            return render(request, "memoria/subject_edit.html", context={"form": form})


def subject_statistics(request):
    pass


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
