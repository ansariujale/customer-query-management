from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .ai_service import AIServiceError, fallback_analysis, parse_ai_response
from .models import CustomerQuery


class QueryAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='agent', password='StrongPass@123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.query = CustomerQuery.objects.create(
            created_by=self.user,
            customer_name='Rahul Sharma',
            email='rahul@example.com',
            subject='Payment issue',
            description='My payment has been deducted twice, but my subscription is still not activated.',
        )

    def test_requires_authentication(self):
        self.client.credentials()  # remove token
        response = self.client.get('/api/queries/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_query(self):
        data = {
            'customer_name': 'Priya Verma',
            'email': 'priya@example.com',
            'subject': 'Cannot login',
            'description': 'I am not able to login to my account since yesterday.',
        }
        response = self.client.post('/api/queries/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'Pending')
        self.assertEqual(CustomerQuery.objects.count(), 2)

    def test_create_query_invalid_data(self):
        data = {
            'customer_name': 'A',
            'email': 'not-an-email',
            'subject': 'Hi',
            'description': 'short',
        }
        response = self.client.post('/api/queries/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('description', response.data)

    def test_list_queries(self):
        response = self.client.get('/api/queries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_user_cannot_see_other_users_query(self):
        other = User.objects.create_user(username='other', password='StrongPass@123')
        other_query = CustomerQuery.objects.create(
            created_by=other, customer_name='Someone', email='x@example.com',
            subject='Other query', description='This belongs to another user.',
        )
        response = self.client.get(f'/api/queries/{other_query.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_query_detail(self):
        response = self.client.get(f'/api/queries/{self.query.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['customer_name'], 'Rahul Sharma')

    def test_update_query(self):
        data = {
            'customer_name': 'Rahul Sharma',
            'email': 'rahul.new@example.com',
            'subject': 'Payment issue updated',
            'description': 'Payment deducted twice, please check urgently.',
            'category': 'Billing',
            'priority': 'High',
            'status': 'In Progress',
        }
        response = self.client.put(f'/api/queries/{self.query.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.query.refresh_from_db()
        self.assertEqual(self.query.email, 'rahul.new@example.com')
        self.assertEqual(self.query.status, 'In Progress')

    def test_update_status(self):
        response = self.client.patch(f'/api/queries/{self.query.id}/status/', {'status': 'Resolved'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.query.refresh_from_db()
        self.assertEqual(self.query.status, 'Resolved')

    def test_update_status_invalid(self):
        response = self.client.patch(f'/api/queries/{self.query.id}/status/', {'status': 'Closed'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_query(self):
        response = self.client.delete(f'/api/queries/{self.query.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CustomerQuery.objects.filter(id=self.query.id).exists())

    def test_search_and_filter(self):
        CustomerQuery.objects.create(
            created_by=self.user, customer_name='Amit', email='amit@example.com',
            subject='App crash', description='The app crashes when I open settings.',
            category='Technical', status='Resolved',
        )
        response = self.client.get('/api/queries/?search=amit')
        self.assertEqual(response.data['count'], 1)

        response = self.client.get('/api/queries/?category=Technical&status=Resolved')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['customer_name'], 'Amit')

    def test_dashboard(self):
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['pending'], 1)
        self.assertEqual(response.data['resolved'], 0)

    @patch('queries.ai_service.call_gemini')
    def test_analyze_with_gemini(self, mock_gemini):
        mock_gemini.return_value = (
            '{"category": "Billing", "priority": "High", '
            '"suggested_response": "We apologise for the inconvenience."}'
        )
        response = self.client.post(f'/api/queries/{self.query.id}/analyze/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ai_used'], 'gemini')

        self.query.refresh_from_db()
        self.assertEqual(self.query.category, 'Billing')
        self.assertEqual(self.query.priority, 'High')
        self.assertEqual(self.query.analysed_by, 'gemini')

    @patch('queries.ai_service.call_gemini')
    def test_analyze_uses_fallback_when_ai_fails(self, mock_gemini):
        mock_gemini.side_effect = AIServiceError('service down')
        response = self.client.post(f'/api/queries/{self.query.id}/analyze/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['ai_used'], 'fallback')
        self.assertEqual(response.data['analysis']['category'], 'Billing')
        self.assertEqual(response.data['analysis']['priority'], 'High')


class AIServiceTests(APITestCase):

    def test_parse_handles_code_block_and_lowercase(self):
        text = '```json\n{"category": "billing", "priority": "high", "suggested_response": "Sorry!"}\n```'
        result = parse_ai_response(text)
        self.assertEqual(result['category'], 'Billing')
        self.assertEqual(result['priority'], 'High')

    def test_parse_invalid_values_get_defaults(self):
        text = '{"category": "Shipping", "priority": "Critical", "suggested_response": ""}'
        result = parse_ai_response(text)
        self.assertEqual(result['category'], 'General')
        self.assertEqual(result['priority'], 'Medium')
        self.assertTrue(result['suggested_response'])

    def test_parse_invalid_json(self):
        with self.assertRaises(AIServiceError):
            parse_ai_response('this is not json')

    def test_fallback_login_issue(self):
        result = fallback_analysis('Login problem', 'I cannot login to my account')
        self.assertEqual(result['category'], 'Account Related')
        self.assertEqual(result['priority'], 'High')
