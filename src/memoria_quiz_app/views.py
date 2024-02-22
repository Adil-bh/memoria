from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.shortcuts import render, redirect

from memoria_quiz_app.forms import UserRegistrationForm


def signup(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("home")
    else:
        form = UserRegistrationForm()

    return render(request, "memoria/signup.html", context={"form": form})


def home(request):
    return HttpResponse('<h1>blog</h1>')


def about(request):
    return render(request, "about.html")


def privacy(request):
    return render(request, "privacy.html")


def legals(request):
    return render(request, "legals.html")