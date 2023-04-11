"""URL mappings for the user app(API)"""
from django.urls import path
from user import views

app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/',views.createTokenView.as_view(), name='token'),
] # corresponding to the file test_user_api.py, reverse()...