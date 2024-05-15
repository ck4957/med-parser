from rest_framework import serializers
from .models import MedicationStatement

class MedicationStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationStatement
        fields = ['id', 'statement_text']

