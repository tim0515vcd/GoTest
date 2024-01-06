from django.urls import path
from questionbank.views import QuestionBankView, QuestionsView

urlpatterns = [
    path("", QuestionBankView.as_view(), name="questionbank"),
    path("<int:pk>", QuestionsView.as_view(), name="questions"),
]
