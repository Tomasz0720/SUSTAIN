from django.urls import path
from .views import process_query, solve_math, optimize_text, token_length

urlpatterns = [
    path('process_query/', process_query, name='process_query'),
    path('solve_math/', solve_math, name='solve_math'),
    path('optimize_text/', optimize_text, name='optimize_text'),
    path('token_length/', token_length, name='token_length'),
]