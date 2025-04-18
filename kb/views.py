from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import DataSource
from chat.pinecone import chunk_text, PineconeClient
from django.db import transaction
import uuid
from .utils import extract_pdf_text, extract_docx_text, extract_txt_text, extract_text_from_url
import logging
import json
import os
from django.utils.text import slugify

from chat.models import Chatbot

import tempfile



@login_required
def dashboard(request):
    chatbots = Chatbot.objects.filter(user=request.user)
    return render(request, 'dashboard/dashboard.html', {'chatbots': chatbots})



def create_chatbot_page(request):
    return render(request, 'dashboard/create_chatbot.html')



def edit_chatbot_page(request, chatbot_id):
    return render(request, 'dashboard/chatbot_detail.html')





















