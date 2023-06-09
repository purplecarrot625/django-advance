"""Serializers for the recipe app."""

from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredient objects"""
    class Meta:
        model = Ingredient  # Model that the ingredient serializer is based on
        fields = ['id', 'name']
        read_only_fields = ['id']

class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for recipes"""
    tags = TagSerializer(many=True, required=False)  # many=True, because we are serializing a list of objects
    ingredients = IngredientSerializer(many=True, required=False)
    class Meta:
        #  Set the model
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags',
                  'ingredients']
        read_only_fields = ['id']
    def _get_or_create_tags(self, tags, recipe):
        """Handle getting or creating tag as needed, internal method不会在其他地方被调用"""
        auth_user = self.context['request'].user  # HTTPrequest 对象中，可以得到当前请求用户
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self, ingredients, recipe):
        """ Handle getting or creating ingredients as needed"""
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient,
            )
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        """Create a recipe"""
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)

        #  Get an existing tag or create a new tag
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)

        return recipe

    def update(self, instance, validated_data):
        """Update a recipe"""
        tags = validated_data.pop('tags', None)
        ingredient = validated_data.pop('ingredients', None)

        # If tag is an empty list, clear all the tags
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        # If ingredient is an empty list, clear all the ingredients
        if ingredient is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredient, instance)

        # Rest of the data (except tags), reassign to the instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance



class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']

class RecipeImageSerializer(serializers.ModelSerializer):
    """ Serializer for uploading images to recipes"""

    class Meta:
        model = Recipe # Link to the recipe model
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': True}}  #  extra_kwargs: 用于指定特定字段的额外参数，这里指定了image字段是必须的
