"""
Views for the user API
"""
from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user.serializers import UserSerializer, AuthTokenSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""
    serializer_class = UserSerializer # This is the serializer class that will be used to create the object

class createTokenView(ObtainAuthToken):
    """Create a new auth token for user"""
    serializer_class = AuthTokenSerializer  # use our custom user model
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES  # use the default renderer classes