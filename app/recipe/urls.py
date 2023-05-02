"""
URL mappings for the recipe app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from recipe import views

router = DefaultRouter()
router.register('recipes', views.RecipeViewSet)  # create an endpoint: api/recipes
router.register('tags', views.TagViewSet)  # create an endpoint: api/tags
router.register('ingredients', views.IngredientViewSet)  # create an endpoint: api/ingredients
app_name = 'recipe'  # namespace for the urls
urlpatterns = [
    path('', include(router.urls)),
]
