import ast
import datetime
import json
import random

import openai

from memoria_quiz_app.models import Questions


def generate_question(user, subject, difficulty):
    user_to_ask = user
    url_subject = subject
    if url_subject == "subject1":
        subject = user_to_ask.subject1
    elif url_subject == "subject2":
        subject = user_to_ask.subject2
    else:
        subject = "Culture générale, gastronomie, histoire, géographie, sciences, musique, etc."
    response = openai.chat.completions.create(
        #model="gpt-4-turbo-preview",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=3000,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": f"""
        Tu es un assistant IA spécialisé dans la génération de questions de quiz. 
        Ton rôle est de poser des questions pertinentes et stimulantes pour tester les connaissances des utilisateurs sur différents sujets. 
        Les questions sont à choix multiples (QCM). Pour les questions de type QCM, tu devras fournir quatre options de réponse possibles.
        Les questions que tu poses doivent être adaptées au niveau de difficulté spécifié par l'utilisateur. 
        Un niveau de difficulté plus élevé signifie que les questions doivent être plus complexes et plus détaillées.
        Ton prochain message sera une réponse JSON contenant 20 questions sur le sujet "{subject}". Le niveau de difficulté pour ce sujet est "{difficulty}". 

        La réponse doit être au format JSON et doit inclure la question, le type de question (QCM), les options de réponse (pour les questions de type QCM) et la bonne réponse. Voici un exemple de format de réponse :
        - Pour une question de type QCM :
            "question": "Quelle est la principale fonction de la boucle 'for' en Python ?",
            "type": "QCM",
            "options": ["Répéter une action un nombre défini de fois", "Répéter une action tant qu'une condition est vraie", "Effectuer une action directement", "Répéter une action un nombre indéfini de fois"],
            "answer": "Répéter une action un nombre défini de fois",
            "explanation": "La boucle 'for' en Python est utilisée pour répéter une action un nombre défini de fois."
        """}]
    )

    print(response.choices[0].message.content)
    json_response = json.loads(response.choices[0].message.content)
    questions_list = json_response['questions']
    return json.dumps({"questions": questions_list}, ensure_ascii=False).encode('utf-8')


    # question = json_response['question']
    # question_type = json_response['type']
    # explication = json_response.get('explanation')
    #Si la question est de type QCM
    # if question_type == "QCM":
    #     expected_answer = json_response['answer']
    #     options = json_response.get('options')
    #     return json.dumps({"question": question, "type": question_type, "options": options, "answer": expected_answer, "explication": explication},
    #                   ensure_ascii=False).encode('utf-8')


def question_creation(user: object, subject: str, question: str, question_type: str, options: list, explication: str, expected_answer: str):
    question = Questions(user=user,
                         question=question,
                         question_type=1 if question_type == "QCM" else 0,
                         expected_answer=expected_answer if question_type == "QCM" else None,
                         options=options if question_type == "QCM" else None,
                         explication_answer=explication,
                         subject=subject)
    question.save()


# Vérifier si l'utilisateur a déjà répondu à une question depuis la création de son compte
def user_has_question(user: object):
    return True if Questions.objects.filter(user=user).exists() else False


def check_answer_and_scoring(user: object, question: object, subject: str, question_type: str):
    if subject == "subject1":
        # Check if the user's answer is correct
        if question.user_answer == question.expected_answer:
            user.number_valid_answers_s1 += 1
            question.is_answer_valid = True
            user.win_streak_subject1 += 1
            user.save()
        # If the user's answer is incorrect
        elif question.user_answer != question.expected_answer:
            question.is_answer_valid = False
            user.win_streak_subject1 = 0
        user.number_answered_questions_s1 += 1
        user.save()
    elif subject == "subject2":
        if question.user_answer == question.expected_answer:
            user.number_valid_answers_s2 += 1
            question.is_answer_valid = True
            user.win_streak_subject2 += 1
            user.save()
        elif question.user_answer != question.expected_answer:
            question.is_answer_valid = False
            user.win_streak_subject2 = 0
        user.number_answered_questions_s2 += 1
        user.save()
    else:
        if question.user_answer == question.expected_answer:
            user.number_valid_answers_general_culture += 1
            question.is_answer_valid = True
            user.win_streak_general_culture += 1
            user.save()
        elif question.user_answer != question.expected_answer:
            question.is_answer_valid = False
            user.win_streak_general_culture = 0
        user.number_answered_questions_general_culture += 1
        user.save()


# Choisir le niveau de difficulté en fonction du sujet
def select_difficulty(user: object, subject: str):
    if subject == "subject1":
        return user.difficulty_subject1
    elif subject == "subject2":
        return user.difficulty_subject2
    else:
        return user.difficulty_general_culture


# Vérifier si l'utilisateur peut jouer
def can_user_play(url_subject: str, subject: str, date_last_question: datetime.date):
    if url_subject == subject and date_last_question == None:
        return True
    elif url_subject == subject and date_last_question < datetime.date.today():
        return True
    else:
        return False


# Reset le paramètre is_answered_question à False
def reset_is_answered_question_bool(subject: str, question: object):
        question.is_question_answered = False
        question.save()


def reset_win_streak(user: object, subject: str, new_topic: str, old_topic: str):
    if subject == "subject1" and new_topic != old_topic:
        user.win_streak_subject1 = 0
    elif subject == "subject2" and new_topic != old_topic:
        user.win_streak_subject2 = 0
    else:
        return None


def return_subject_quiz_page(subject: str):
    if subject == "subject1":
        return "quiz_page/quiz_subject1_page.html"
    elif subject == "subject2":
        return "quiz_page/quiz_subject2_page.html"
    elif subject == "general_culture":
        return "quiz_page/quiz_general_culture_page.html"


def return_subject_quiz_url(subject: str):
    if subject == "subject1":
        return "subject1"
    elif subject == "subject2":
        return "subject2"
    elif subject == "general_culture":
        return "general_culture"


def format_answer_options(subject: str, context: dict):
        return ast.literal_eval(context["question"].options_subject1)


def return_subject_question_type(question ,subject):
    if subject == "subject1":
        return question.question_type_subject1
    elif subject == "subject2":
        return question.question_type_subject2
    else:
        return question.question_type_general_culture

