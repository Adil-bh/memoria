"""
URL configuration for memoria project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from memoria_quiz_app import views
from memoria_quiz_app.views import signup, SubjectEdit, QuizGenerator, SubjectChoice
import django.contrib.auth.urls

app_name = "memoria"

urlpatterns = [
    path('', views.home, name="home"),
    path('about/', views.about, name="about"),
    path('privacy/', views.privacy, name="privacy"),
    path('legals/', views.legals, name="legals"),
    path("account/", include("django.contrib.auth.urls")),
    path('account/signup/', signup, name="signup"),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('subjects/index/', SubjectChoice.as_view(), name='index-subjects'),
    path('subjects/edit/<int:pk>', SubjectEdit.as_view(), name="edit-subjects"),
    path('subjects/quiz/<str:subject>', QuizGenerator.as_view(), name='quiz')
]
