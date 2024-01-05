from django.contrib import admin
from questionbank.models import QuestionBank, Question, Answer, Choice

# Register your models here.
admin.site.register(QuestionBank)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Choice)
