from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse


def index(request):
    return HttpResponse("Hello, world. You're at the base index.")

def analyze(request):

    return JsonResponse({'extract_entities'})
