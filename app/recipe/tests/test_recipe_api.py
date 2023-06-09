from decimal import Decimal

import tempfile
import os
from PIL import Image

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail url, contains a unique id"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """ Create and return an image upload url """
    return reverse('recipe:recipe-upload-image', args=[recipe_id])
"""
在这个函数中，reverse函数被传入了一个名称为'recipe:recipe-upload-image'的URL模式，以及一个参数[recipe_id]。
这个URL模式的含义是：它匹配到一个以/recipe/{recipe_id}/image/upload/形式的URL，其中{recipe_id}部分是一个动态参数，
将被传入recipe_id的实际值进行替换。
这个URL表示上传指定食谱ID的图片的URL。
"""

def create_recipe(user, **params):
    """Create and return a sample recipe"""

    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
        'description': 'Sample description',
        'link': 'http://www.example.com',
    }

    defaults.update(params)  # update defaults with params

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(**params)

class PublicRecipeAPITests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call api"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    """Test authenticated recipe API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email = 'user@example.com', password = 'testpass123')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        # create 2 recipes
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)  # 服务器得到的结果

        recipes = Recipe.objects.all().order_by('-id')  # 数据库中的结果
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes returned is for authenticated user"""
        other_user = create_user(email = 'other@example.com', password = 'password123')
        create_recipe(user=other_user) # create a recipe for the other user
        create_recipe(user=self.user) # create a recipe for the authenticated user

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)  # filter by user
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(serializer.data, res.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00,
            'description': 'Sample description',
            'link': 'http://www.example.com',
        }
        res = self.client.post(RECIPES_URL, payload) # api/recipes/recipe
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        original_link = 'http://www.example.com'
        recipe = create_recipe(
            user = self.user,
            title = 'Sample recipe',
            link = original_link,
        )

        payload = {'title':'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()  # by defalut, django will not refresh the object from db
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of a recipe"""
        recipe = create_recipe(
            user = self.user,
            title = 'Sample recipe',
            link = 'http://www.example.com',
            description = 'Sample description',
        )

        payload = {
            'title': 'New recipe title',
            'time_minutes': 10,
            'price': 5.00,
            'description': 'New description',
            'link': 'http://www.example1.com',
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the user is not allowed"""
        new_user = create_user(email = 'user2@example.com', password = 'testpass123')
        recipe = create_recipe(user=self.user)

        payload = {'user': 'new_user.id'}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        new_user = create_user(email = 'user2@example.com', password = 'testpass123')
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00,
            'description': 'New description',
            'link': 'http://www.example1.com',
            'tags':[{'name':'Vegan'}, {'name':'Dessert'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)  # make sure only one recipe is created
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)  # make sure two tags are created
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        tag_Chinese = Tag.objects.create(user=self.user, name='Chinese')
        payload = {
            'title': 'Beijing Roast Duck',
            'time_minutes': 10,
            'price': 5.00,
            'description': 'New description',
            'link': 'http://www.example1.com',
            'tags':[{'name':'Chinese'}, {'name':'Beijing'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_Chinese, recipe.tags.all())  # make sure the specified tag is in the recipe

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()

            self.assertTrue(exists)
    def test_create_tag_on_update(self):
        """Test creating tag whrn updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {
            'tags': [{'name':'Vegan'}]
        }
        url = detail_url(recipe.id)
        # should only be changing the new tag
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Vegan')
        self.assertIn(new_tag, recipe.tags.all())
        #  since the .all() is a new query, no need to refresh the db

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        #  Changing breakfast to lunch tag
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())  #tag_lunch is updated
        self.assertNotIn(tag_breakfast, recipe.tags.all())  #tag_breakfast is removed

    def test_clear_recipe_tags(self):
        """Test cleaning a recipe tag"""
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients"""

        payload = {
            'title': 'Sample recipe',
            'time_minutes': 10,
            'price': 5.00,
            'ingredients':[{'name':'Cucumber'}, {'name':'Salt'}],
            'description': 'New description',
            'link': 'http://www.example1.com',
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """ Test creating a new recipe with existing ingredient. """
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {
            'title': 'Lemonade',
            'time_minutes': 10,
            'price': 5.00,
            'ingredients': [{'name':'Lemon'}, {'name':'Sugar'}],
            'description': 'New description',
            'link': 'http://www.example1.com',
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]  # get recipe from the results
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()

            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """ Test creating an ingredient when updating a recipe. """

        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [{'name':'Lemon'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Lemon')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """ Test clearing a recipe's ingredients. """
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)

    def test_filter_recipes_by_tags(self):
        """ Test filtering recipes by tags. """
        r1 = create_recipe(user=self.user, title='Thai vegetable curry')
        r2 = create_recipe(user=self.user, title='Aubergine with tahini')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user=self.user, title='Fish and chips')

        params = {'tags': f'{tag1.id},{tag2.id}'} # f-string
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """ Test filtering ingredients by tags. """
        r1 = create_recipe(user=self.user, title='Posh beans on toast')
        r2 = create_recipe(user=self.user, title='Chicken cacciatore')
        i1 = Ingredient.objects.create(user=self.user, name='Feta cheese')
        i2 = Ingredient.objects.create(user=self.user, name='Chicken')
        r1.ingredients.add(i1)
        r2.ingredients.add(i2)
        r3 = create_recipe(user=self.user, title='Steak and mushrooms')

        params = {'ingredients': f'{i1.id},{i2.id}'} # f-string
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    # Delete the image after the test
    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """ Test uploading an image to recipe. """
        url = image_upload_url(self.recipe.id)

        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            image = Image.new('RGB', (10,10))
            image.save(image_file, format='JPEG')
            image_file.seek(0)  # move the pointer to the beginning of the file
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """ Test uploading an invalid image. """
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image':'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
