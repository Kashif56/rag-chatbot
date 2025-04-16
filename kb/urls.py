from django.urls import path
from . import views

app_name = 'kb'

urlpatterns = [
    path('add-data-source/', views.add_data_source, name='add_data_source'),
    path('data-source/<int:data_source_id>/', views.view_data_source_detail, name='view_data_source'),
    path('download/<int:data_source_id>/', views.download_data_source, name='download_data_source'),
    path('delete/<int:data_source_id>/', views.delete_data_source, name='delete_data_source'),
]

