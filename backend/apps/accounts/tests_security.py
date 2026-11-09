from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient


@override_settings(SECURE_SSL_REDIRECT=False)
class AccountSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('owner', password='Old-Example-9831!', email='owner@example.test')
        self.other = get_user_model().objects.create_user('other', email='private@example.test')
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_list_never_exposes_another_email(self):
        response = self.client.get('/api/v1/accounts/users/')
        self.assertEqual(response.status_code, 200)
        other = next(row for row in response.data if row['id'] == self.other.pk)
        self.assertNotIn('email', other)

    def test_generic_update_cannot_store_raw_password(self):
        response = self.client.patch(f'/api/v1/accounts/users/{self.user.pk}/', {'password': 'New-Example-5823!'})
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Old-Example-9831!'))

    def test_change_requires_old_password_and_hashes_new_one(self):
        endpoint = '/api/v1/accounts/users/cambiar-password/'
        self.assertEqual(self.client.post(endpoint, {'old_password': 'wrong', 'new_password': 'New-Example-5823!'}).status_code, 400)
        response = self.client.post(endpoint, {'old_password': 'Old-Example-9831!', 'new_password': 'New-Example-5823!'})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.password, 'New-Example-5823!')
        self.assertTrue(self.user.check_password('New-Example-5823!'))
