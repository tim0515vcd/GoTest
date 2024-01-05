from django.db import models
from account.models import Account


# Create your models here.
class QuestionBank(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField("題庫類別", max_length=100, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    QUESTION_TYPES = (
        ("single_choice", "單選題"),
        ("multiple_choice", "複選題"),
        ("short_answer", "簡答題"),
        ("true_false", "是非題"),
    )

    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text


class Answer(models.Model):
    """簡答題、是非題

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    anser = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class Choice(models.Model):
    """選擇題、複選題

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.TextField(blank=True)
    anser = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text
