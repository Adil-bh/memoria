from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.utils.translation import gettext_lazy as _

from memoria_quiz_app.forms import UserRegistrationForm
from .tokens import account_activation_token


def activate(request, uidb64, token):
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
        return redirect("login")
    else:
        messages.error(request, "Lien d'activation invalide.")
    return redirect('home')


def activateEmail(request, user, to_email):
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
            return redirect("home")
    else:
        form = UserRegistrationForm()

    return render(request, "memoria/signup.html", context={"form": form})


def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def privacy(request):
    return render(request, "privacy.html")


def legals(request):
    return render(request, "legals.html")
