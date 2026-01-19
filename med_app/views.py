from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import spacy
import medspacy
from medspacy.visualization import visualize_ent
import os

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
        'entities': entities,
        'model': 'medspacy'
        #'medication_info': medication_info
    }

    return Response(response_data)


@api_view(['POST'])
def parse_medical_text_gemma(request):
    """
    Parse medical text using Google's MedGemma model.
    This endpoint uses the Gemini API with medical-specific prompting.
    """
    text = request.data.get('medical_text')
    
    if not text:
        return Response({'error': 'medical_text is required'}, status=400)
    
    try:
        import google.generativeai as genai
        
        # Configure the API key from environment variable
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            return Response({
                'error': 'GOOGLE_API_KEY environment variable not set',
                'message': 'Please set GOOGLE_API_KEY to use MedGemma'
            }, status=500)
        
        genai.configure(api_key=api_key)
        
        # Use Gemini model (MedGemma functionality)
        model = genai.GenerativeModel('gemini-pro')
        
        # Craft a medical entity extraction prompt
        prompt = f"""You are a medical text parser. Extract medical entities from the following text and categorize them.

Text: "{text}"

Extract entities in the following categories:
- DRUG: Medication names
- DOSAGE: Medication dosages (e.g., 500mg, 10ml)
- FREQUENCY: How often medication is taken (e.g., twice daily, every 4 hours)
- DURATION: How long treatment lasts (e.g., for 7 days, 2 weeks)
- CONDITION: Medical conditions or diagnoses
- PROCEDURE: Medical procedures

Respond ONLY with a JSON array of entities in this exact format:
[["entity_text", "CATEGORY"], ["entity_text", "CATEGORY"]]

Example: [["Metformin", "DRUG"], ["500mg", "DOSAGE"], ["twice daily", "FREQUENCY"]]
"""
        
        # Generate response
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse the JSON response
        import json
        import re
        
        # Extract JSON array from response (handle markdown code blocks)
        json_match = re.search(r'\[\[.*?\]\]', response_text, re.DOTALL)
        if json_match:
            entities_json = json_match.group(0)
            entities = json.loads(entities_json)
        else:
            # Try to parse the entire response
            try:
                entities = json.loads(response_text)
            except:
                entities = []
        
        response_data = {
            'entities': entities,
            'model': 'medgemma',
            'raw_response': response_text[:500]  # Include first 500 chars for debugging
        }
        
        return Response(response_data)
        
    except ImportError:
        return Response({
            'error': 'google-generativeai package not installed',
            'message': 'Install it with: pip install google-generativeai'
        }, status=500)
    except Exception as e:
        return Response({
            'error': str(e),
            'message': 'Error processing with MedGemma'
        }, status=500)