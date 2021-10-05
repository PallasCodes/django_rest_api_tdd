import os
import tempfile

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase


from rest_framework import status
from rest_framework.test import APIClient

from PIL import Image

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import IngredientSerializer, RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def sample_recipe(user, **params):
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)

def sample_ingredient(user, name='Cinnamon'):
    return Ingredient.objects.create(user=user, name=name)

def sample_tag(user, name='Main course'):
    return Tag.objects.create(user=user, name=name)

def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'tester@gmail.com',
            'pass1234'
        )
        self.client.force_authenticate(self.user)


    def test_retrieve_recipes(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_recipies_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            'other@gmail.com',
            'password1234'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)


    def test_view_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)


    def test_create_basic_recipe(self):
        payload = {
            'title': 'Test recipe',
            'time_minutes': 30,
            'price': 10.00
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    
    def test_create_recipe_with_tags(self):
        tag1 = sample_tag(user=self.user, name='Tag 1')
        tag2 = sample_tag(user=self.user, name='Tag 2')
        payload = {
           'title': 'Test recipe witht tags',
            'time_minutes': 30,
            'price': 10.00,
            'tags': [tag1.id, tag2.id]
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)


    def test_create_recipe_with_ingredients(self):
        ingredient1 = sample_ingredient(user=self.user, name='ingredient 1')
        ingredient2 = sample_ingredient(user=self.user, name='ingredient 2')
        payload = {
           'title': 'Test recipe witht ingredients',
            'time_minutes': 30,
            'price': 10.00,
            'ingredients': [ingredient1.id, ingredient2.id]
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)


    def test_filter_recipes_by_tags(self):
        recipe1 = sample_recipe(user=self.user, title='Tacos')
        recipe2 = sample_recipe(user=self.user, title='Pizza')
        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(user=self.user, title='Fish and chips')

        res = self.client.get(
            RECIPES_URL,
            {'tags': '{},{}'.format(tag1.id, tag2.id)}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    
    def test_filter_recipes_by_ingredients(self):
        recipe1 = sample_recipe(user=self.user, title='Tacos')
        recipe2 = sample_recipe(user=self.user, title='Pizza')
        ingredient1 = sample_ingredient(user=self.user, name='Milk')
        ingredient2 = sample_ingredient(user=self.user, name='Cheese')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(user=self.user, title='Fish and chips')

        res = self.client.get(
            RECIPES_URL,
            {'ingredients': '{},{}'.format(ingredient1.id, ingredient2.id)}
        )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    
class RecipeImageUpload(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('user', 'testpassword')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)


    def tearDown(self):
        self.recipe.image.delete()


    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            
            res = self.client.post(url, { 'image': ntf }, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    
    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)

        res = self.client.post(url, { 'image': 'notimage' }, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
