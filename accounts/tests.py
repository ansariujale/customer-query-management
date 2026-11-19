from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class AuthTests(APITestCase):

    def test_register_user(self):
        data = {
            'username': 'john',
            'email': 'john@example.com',
            'password': 'StrongPass@123',
            'confirm_password': 'StrongPass@123',
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertTrue(User.objects.filter(username='john').exists())

    def test_register_password_mismatch(self):
        data = {
            'username': 'john',
            'email': 'john@example.com',
            'password': 'StrongPass@123',
            'confirm_password': 'Different@123',
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        data = {
            'username': 'john',
            'email': 'john@example.com',
            'password': '123',
            'confirm_password': '123',
        }
        response = self.client.post('/api/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        User.objects.create_user(username='john', password='StrongPass@123')
        response = self.client.post('/api/login/', {'username': 'john', 'password': 'StrongPass@123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_login_wrong_password(self):
        User.objects.create_user(username='john', password='StrongPass@123')
        response = self.client.post('/api/login/', {'username': 'john', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
