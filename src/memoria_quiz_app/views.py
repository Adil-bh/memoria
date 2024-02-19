from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return HttpResponse('<h1>blog</h1>')


def about(request):
    return render(request,"about.html")


def privacy(request):
    return render(request, "privacy.html")


def legals(request):
    return render(request,"legals.html")