# models.py
from django.db import models

class MedicationStatement(models.Model):
    statement_text = models.TextField()

# serializers.py
# views.py
