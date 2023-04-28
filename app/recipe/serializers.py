"""Serializers for the recipe app."""

from rest_framework import serializers
from core.models import Recipe, Tag

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes"""
    tags = TagSerializer(many=True, required=False)  # many=True, because we are serializing a list of objects
    class Meta:
        #  Set the model
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
        read_only_fields = ['id']
    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tag as needed"""
        auth_user = self.context['request'].user  # HTTPrequest 对象中，可以得到当前请求用户
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags = validated_data.pop('tags', None)

        # If tag is an empty list, clear all the tags
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        # Rest of the data (except tags), reassign to the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance



class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
