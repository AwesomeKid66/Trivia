# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Question(models.Model):
    id = models.AutoField(primary_key=True)
    topic = models.TextField(blank=True, null=True)
    question = models.TextField(blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    likelihood = models.IntegerField(default=3)

    class Meta:
        db_table = "questions"
        app_label = "trivia_app"


class Progress(models.Model):
    STATUS_CHOICES = [
        ("unanswered", "Unanswered"),
        ("wrong", "Wrong"),
        ("correct", "Correct"),
    ]

    user_name = models.CharField(max_length=100)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, db_column="question_id")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unanswered")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "progress"  # table will be created by Django
        unique_together = ("user_name", "question")
        app_label = "trivia_app"

    def __str__(self):
        return f"{self.user_name} - {self.question} ({self.status})"