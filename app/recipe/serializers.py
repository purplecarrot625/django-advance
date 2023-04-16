"""Serializers for the recipe app."""

from rest_framework import serializers
from core.models import Recipe

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes"""

    class Meta:
        #  set the model
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']