from django.urls import path
from questionbank.views import QuestionCategoryView

urlpatterns = [
    path("questioncategory/", QuestionCategoryView.as_view(), name="questioncategory"),
]
