"""Test for the ingredients API"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Recipe
)
from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')

#  Helper function
def detail_url(ingredient_id):
    """ Create and return an ingredient detail URL """
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='user@example.com', password='test123'):
    return get_user_model().objects.create_user(email=email, password=password)

class PublicIngredientsApiTests(TestCase):
    """Test unauthenticated API requests"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for reviewing ingredients"""

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientsApiTests(TestCase):
    """Test authenticated API requests"""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True) # many=True because we are serializing a list of objects, many items
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test that ingredients returned are for the authenticated user"""
        user2 = create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='salt')
        ingredient = Ingredient.objects.create(user=self.user, name='tumeric')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1) # only one ingredient
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredients(self):
        """ Test updating an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='potato')

        payload = {'name': 'carrot'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """ Test deleting an ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='potato')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """ Test listing ingredients by those assigned to recipes"""
        ingredient1 = Ingredient.objects.create(user=self.user, name='potato')
        ingredient2 = Ingredient.objects.create(user=self.user, name='carrot')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Potato soup',
            time_minutes=10,
            price=Decimal('5.00'),
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1}) # 1 means True

        s1 = IngredientSerializer(ingredient1)
        s2 = IngredientSerializer(ingredient2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_ingredients_assigned_unique(self):
        """ Test filtering ingredients by assigned returns unique items"""
        ing = Ingredient.objects.create(user=self.user, name='potato')
        Ingredient.objects.create(user=self.user, name='carrot')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Potato soup',
            time_minutes=10,
            price=Decimal('5.00'),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='Carrot soup',
            time_minutes=10,
            price=Decimal('5.00'),
        )

        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1) # only one ingredient