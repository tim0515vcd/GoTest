from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from questionbank.models import Question, QuestionBank, Answer, Choice
from questionbank.serializers import QuestionBankSerializer, QuestionSerializer
from django.db.models import Count

# Create your views here.


class QuestionBankView(generics.GenericAPIView):
    """[題庫選擇]"""

    permission_classes = (IsAuthenticated,)
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    serializer_class = QuestionBankSerializer

    def get_object(self):
        return QuestionBank.objects.filter(account=self.request.user).annotate(
            question_count=Count("questions")
        )

    def get(self, request):
        """[題庫選擇]

        Returns:
            render : question_category.html
        """
        return Response(
            template_name="question_bank.html",
            data={
                "question_bank": self.get_object(),
            },
        )

    def post(self, request):
        """[建立題庫]

        Args:
            request (_type_): _description_

        Returns:
            _type_: _description_
        """
        serializer = self.get_serializer(
            data={"name": request.POST.get("name"), "account": request.user.id}
        )
        if not serializer.is_valid():
            return Response(
                {
                    "result": _("PARAMETER_ERROR"),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()

        return Response({"result": _("Create success")}, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """[刪除題庫]

        Args:
            request (_type_): _description_
            pk (int): 欲刪除的 QuestionBank 的PK值。

        Returns:
            Response: 刪除操作的回應
        """
        try:
            question_bank = QuestionBank.objects.get(pk=pk, account=self.request.user)
        except QuestionBank.DoesNotExist:
            return Response(
                {"result": _("QUESTION_BANK_NOT_FOUND")},
                status=status.HTTP_404_NOT_FOUND,
            )

        question_bank.delete()
        return Response(
            {"result": _("Question bank deleted successfully")},
            status=status.HTTP_200_OK,
        )


class QuestionsView(generics.GenericAPIView):
    """[題庫選擇]"""

    permission_classes = (IsAuthenticated,)
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    serializer_class = QuestionSerializer

    def get_object(self, pk):
        return Question.objects.filter(question_bank=pk)

    def get(self, request, pk):
        """[題庫選擇]

        Returns:
            render : questions.html
        """
        return Response(
            template_name="questions.html",
            data={
                "question_type": Question.QUESTION_TYPES,
                "question_bank": QuestionBank.objects.filter(
                    pk=pk, account=self.request.user
                ).first(),
                "questions": self.get_object(pk=pk),
            },
        )

    def post(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("!!!!!!", serializer.errors)
            return Response(
                {
                    "result": _("PARAMETER_ERROR"),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()

        return Response({"result": _("Create success")}, status=status.HTTP_200_OK)
