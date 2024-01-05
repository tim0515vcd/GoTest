from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

# Create your views here.


class QuestionCategoryView(generics.GenericAPIView):
    """[題庫選擇]"""

    permission_classes = (IsAuthenticated,)
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        """[題庫選擇]

        Returns:
            render : question_category.html
        """
        # rule_obj = IndexInfo.objects.first()
        return Response(
            template_name="question_category.html",
            data={
                "question_category": False,
            },
        )
