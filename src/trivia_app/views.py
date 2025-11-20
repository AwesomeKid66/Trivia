import random

from django.http import JsonResponse
import json
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Import your Question model
from .models import Question, Progress


# Page where user types their name before starting the quiz
def enter_name(request, topic):
    """Page where user types their name before studying"""
    return render(request, "trivia_app/enter_name.html", {"topic": topic})

def study_view(request, topic):
    user_name = request.GET.get("user")
    if not user_name:
        # Redirect to enter name if missing
        return render(request, "trivia_app/enter_name.html", {"topic": topic})

    # Get all questions for the topic
    questions = Question.objects.filter(topic=topic)

    # Build the list to send to template
    data = []
    for q in questions:
        # Check if user already got this question correct
        progress = Progress.objects.filter(user_name=user_name, question=q, status="correct").first()
        if not progress:
            # Include questions the user hasn't answered correctly
            data.append({
                "id": q.id,
                "question": q.question,
                "answer": q.answer,
                "likelihood": q.likelihood,
            })

    return render(request, "trivia_app/study.html", {
        "topic": topic,
        "questions": data,
        "user": user_name,
    })

# Home page template
def index(request):
        # Get unique topics from your questions table
    topics = Question.objects.values_list("topic", flat=True).distinct()
    return render(request, "trivia_app/index.html", {"topics": topics})

def update_progress(request):
    if request.method == "POST":
        # Parse JSON from JS
        data = json.loads(request.body)
        user_name = data.get("user_name")
        question_id = data.get("question_id")
        status = data.get("status")

        # Find the question
        question = get_object_or_404(Question, id=question_id)

        # Get or create progress row
        progress, _ = Progress.objects.get_or_create(user_name=user_name, question=question)
        progress.status = status
        progress.save()

        return JsonResponse({"success": True, "status": progress.status})

    return JsonResponse({"success": False}, status=400)

# API to get all questions
@api_view(["GET"])
@permission_classes([AllowAny])
def get_questions(request):
    data = [{"id": q.id, "question": getattr(q, "question", str(q)), "answer": getattr(q, "answer", ""), "likelihood": getattr(q, "likelihood", 0)}
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
    data = [{"id": q.id, "question": q.question, "answer": q.answer, "likelihood": q.likelihood} for q in qs]
    return Response(data)
