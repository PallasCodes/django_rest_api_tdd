from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, force_authenticate


# endpoints
CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
  return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
  def setUp(self):
    self.client = APIClient()

  def test_create_valid_user_success(self):
    payload = {
      'email': 'test@tester.com',
      'password': 'testpassword',
      'name': 'tester'
    }
    res = self.client.post(CREATE_USER_URL, payload)
    self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    user = get_user_model().objects.get(**res.data)
    self.assertTrue(user.check_password(payload['password']))
    self.assertNotIn('password', res.data)

  def test_user_exists(self):
    payload = {
      'email': 'test@tester.com',
      'password': 'testpassword',
      'name': 'tester'
    }
    create_user(**payload)
    res = self.client.post(CREATE_USER_URL, payload)
    self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

  def test_password_too_short(self):
    payload = {
      'email': 'test@tester.com',
      'password': 'pw',
      'name': 'tester'
    }
    res = self.client.post(CREATE_USER_URL, payload)
    self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    user_exists = get_user_model().objects.filter(email=payload['email']).exists()
    self.assertFalse(user_exists)

  def test_create_token(self):
    payload = {
      'email': 'test123@tester.com',
      'password': 'pw123456',
      'name': 'tester2'
    }
    create_user(**payload)
    res = self.client.post(TOKEN_URL, payload)
    self.assertIn('token', res.data)
    self.assertEqual(res.status_code, status.HTTP_200_OK)

  def test_create_token_invalid_credentials(self):
    create_user(email='test@tester.com', password='testpass')
    payload = {
      'email': 'test@tester.com',
      'password': 'testwrongpassword'
    }
    res = self.client.post(TOKEN_URL, payload)
    self.assertNotIn('token', res.data)
    self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

  def test_create_token_no_user(self):
    payload = {
      'email': 'test@tester.com',
      'password': 'pw123456',
      'name': 'tester'
    }
    res = self.client.post(TOKEN_URL, payload)
    self.assertNotIn('token', res.data)
    self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

  def test_create_token_missing_password(self):
    payload = {
      'email': 'test@tester,com',
      'password': ''
    }
    res = self.client.post(TOKEN_URL, payload)
    self.assertNotIn('token', res.data)
    self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

  def test_retrieve_user_unauthorized(self):
    res = self.client.get(ME_URL)
    self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
  def setUp(self):
    self.user = create_user(
      email = 'tester123@test.com',
      password = 'test123456',
      name = 'tester1234'
    )
    self.client = APIClient()
    self.client.force_authenticate(user=self.user)

  def test_retrieve_profile_sucess(self):
    res = self.client.get(ME_URL)
    self.assertEqual(res.status_code, status.HTTP_200_OK)
    self.assertEqual(res.data, {
      'name': self.user.name,
      'email': self.user.email
    })  
  
  def test_post_me_not_allowed(self):
    res = self.client.post(ME_URL, {})
    self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

  def test_update_user_profile(self):
    payload = {
      'password': 'mypassword',
      'name': 'my name'
    }
    res = self.client.patch(ME_URL, payload)
    self.user.refresh_from_db()
    self.assertEqual(self.user.name, payload['name'])
    self.assertTrue(self.user.check_password(payload['password']))
    self.assertEqual(res.status_code, status.HTTP_200_OK)

