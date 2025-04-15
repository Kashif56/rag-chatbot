from django.urls import path
from . import views

app_name = 'kb'

urlpatterns = [
    path('add-data-source/', views.add_data_source, name='add_data_source'),
]

