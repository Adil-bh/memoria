from django.contrib import admin
from memoria_quiz_app.models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "subject1", "subject2", "difficulty_subject1",
                    "total_answered_questions", "total_valid_answers", "win_rate",)


admin.site.register(CustomUser, CustomUserAdmin)