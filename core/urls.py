from django.urls import path
from .views import index, features, pricing, learning, contact

app_name = 'core'

urlpatterns = [
    path('', index, name='index'),
    path('features/', features, name='features'),
    path('pricing/', pricing, name='pricing'),
    path('learning/', learning, name='learning'),
    path('contact/', contact, name='contact'),
]