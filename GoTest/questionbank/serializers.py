import re

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from questionbank.models import QuestionBank


class QuestionBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionBank
        fields = [
            "account",
            "name",
        ]


class QuestionSerializer(serializers.Serializer):
    question_type = serializers.CharField(required=True)
    question = serializers.CharField(required=True)
    option_list = serializers.ListField(required=False)
    single_choice_answer = serializers.CharField(required=False)
    true_false_answer = serializers.BooleanField(required=False)
    answer_details = serializers.CharField(required=True)
