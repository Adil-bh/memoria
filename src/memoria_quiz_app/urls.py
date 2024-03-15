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
from django.urls import path, include, reverse_lazy

from memoria_quiz_app import views
from memoria_quiz_app.views import signup, SubjectEdit, SubjectChoice, QuizView
from django.contrib.auth import views as auth_views
import django.contrib.auth.urls
import django.contrib.admin.templates.registration
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
    path('subjects/quiz/<str:subject>', QuizView.as_view(), name='quiz'),

    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="registration/password_reset.html", email_template_name="registration/password_reset_email.html"), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),

]
