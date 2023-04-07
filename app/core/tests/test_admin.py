"""
Test for the django admin modifications
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

class AdminSiteTests(TestCase):
    """Test for the django admin."""

    def setUp(self):
       """Create user and client"""
       self.client = Client()
       self.admin_user = get_user_model().objects.create_superuser(
           email='admin@example.com',
           password='test123',
       )
       self.client.force_login(self.admin_user)  # force authentication to the user
       self.user = get_user_model().objects.create_user(
           email='user@example.com',
           password='test123',
           name='Test User',
       )

    def test_user_list(self):
        """Test that users are listed on user page"""
        url = reverse('admin:core_user_changelist')  # get the url for the list user page
        res=self.client.get(url) # get the response from the url

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_user_change_page(self):
        """Test that the user edit page works"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """Test the create user page works"""
        url = reverse('admin:core_user_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)