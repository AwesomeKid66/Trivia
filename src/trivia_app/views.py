import random

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Import your Question model
from .models import Question


# Home page template
def index(request):
    return render(request, "trivia_app/index.html")

# API to get all questions
@api_view(["GET"])
@permission_classes([AllowAny])
def get_questions(request):
    data = [{"id": q.id, "question": getattr(q, "question", str(q)), "answer": getattr(q, "answer", "")}
            for q in Question.objects.all()]
    return Response(data)

# API to check answer
@csrf_exempt  # dev-only convenience
@api_view(["POST"])
@permission_classes([AllowAny])
def check_answer(request, qid):
    try:
        q = Question.objects.get(id=qid)
    except Question.DoesNotExist:
        return Response({"correct": False, "message": "Invalid question"})
    user_answer = (request.data.get("answer") or "").strip().lower()
    correct = (getattr(q, "answer", "") or "").strip().lower() == user_answer
    return Response({"correct": correct})

# Return list of unique topics
@api_view(["GET"])
@permission_classes([AllowAny])
def get_topics(request):
    topics = Question.objects.values_list("topic", flat=True).distinct()
    return Response(sorted(list(topics)))

# Return all questions in a topic (randomized)
@api_view(["GET"])
@permission_classes([AllowAny])
def get_questions_by_topic(request, topic_name):
    qs = list(Question.objects.filter(topic=topic_name))
    random.shuffle(qs)
    data = [{"id": q.id, "question": q.question, "answer": q.answer} for q in qs]
    return Response(data)
