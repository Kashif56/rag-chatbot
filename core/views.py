from django.shortcuts import render
from kb.models import DataSource
from chat.models import Chatbot

# Create your views here.


def index(request):
    return render(request, 'core/index.html')


def features(request):
    return render(request, 'core/features.html')


def pricing(request):
    return render(request, 'core/pricing.html')


def learning(request):
    return render(request, 'core/learning.html')


def contact(request):
    return render(request, 'core/contact.html')
   