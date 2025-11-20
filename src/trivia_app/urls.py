from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("topics/", views.get_topics, name="get_topics"),
    path("questions/<str:topic_name>/", views.get_questions_by_topic, name="get_questions_by_topic"),
    path("study/<str:topic>/enter/", views.enter_name, name="enter_name"),
    path("study/<str:topic>/", views.study_view, name="study"),
    path("update_progress/", views.update_progress, name="update_progress"),
]

