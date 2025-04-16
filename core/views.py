from django.shortcuts import render
from kb.models import DataSource

# Create your views here.


def dashboard(request):
    data_sources = DataSource.objects.filter(user=request.user)
    return render(request, 'core/dashboard.html', {'data_sources': data_sources})