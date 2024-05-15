from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import spacy
import medspacy
from medspacy.visualization import visualize_ent

# Default

# Create your views here.
from django.http import HttpResponse, JsonResponse


def index(request):
    return HttpResponse("Hello, world. You're at the base index.")


@api_view(['POST'])
def parse_medication_statement(request):
    statement_text = request.data.get('statement_text')
    
    # Call your parsing function here
    structured_components = parse_medication_statement(statement_text)
    
    return Response(structured_components)


@api_view(['POST'])
def parse_medical_text(request):
    text = request.data.get('medical_text')
    print(text)
    # Load the spaCy model for medical text processing
    nlp = medspacy.load()

    # Use spaCy to process the medical text and extract entities
    doc = nlp(text)
    print(doc)
    entities = [(ent.text, ent.label_) for ent in doc.ents]

    #visualize_ent(doc)

    # Return the structured components in the API response
    response_data = {
        'entities': entities
        #'medication_info': medication_info
    }

    return Response(response_data)