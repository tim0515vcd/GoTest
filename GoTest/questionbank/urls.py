from django.urls import path
from questionbank.views import QuestionBankView, QuestionsView

urlpatterns = [
    path("", QuestionBankView.as_view(), name="questionbank"),
    path("delete/<int:pk>", QuestionBankView.as_view(), name="delete_questionbank"),
    path("<int:pk>", QuestionsView.as_view(), name="questions"),
    path("create/<int:pk>", QuestionsView.as_view(), name="create_questions"),
]
