from django.urls import path
from . import views

app_name = 'kb'

urlpatterns = [
    path('', views.knowledge_bases, name='knowledge_base'),
    path('<uuid:kb_id>/', views.knowledge_base_detail, name='knowledge_base_detail'),
    path('add-source/<uuid:kb_id>/', views.add_data_source, name='add_data_source'),
    path('delete-source/<int:source_id>/', views.delete_data_source, name='delete_data_source'),
    path('source/<int:source_id>/', views.source_detail, name='source_detail'),
]

