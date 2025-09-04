from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("topics/", views.get_topics, name="get_topics"),
    path("questions/<str:topic_name>/", views.get_questions_by_topic, name="get_questions_by_topic"),
]

