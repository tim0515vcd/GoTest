from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response

# Create your views here.


class IndexView(generics.GenericAPIView):
    """[首頁功能]"""

    permission_classes = (IsAuthenticated,)
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        """[取得首頁]

        Returns:
            render : home.html
        """
        # rule_obj = IndexInfo.objects.first()
        return Response(
            template_name="home.html",
            data={
                # "rule": rule_obj.rule,
            },
        )
