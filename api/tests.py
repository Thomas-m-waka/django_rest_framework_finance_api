from django.test import TestCase

# Create your tests here.
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from .models import Transaction

User = get_user_model()

class TransactionTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

        self.transaction_data = {
            "date": "2024-10-10",
            "amount": 100.00,
            "transaction_type": "income",
            "payment_method": "cash",
            "category": "salary"
        }
        self.url = reverse('transaction_list_create')  # Adjust the URL name as needed

    def test_create_transaction(self):
        response = self.client.post(self.url, self.transaction_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.get().amount, 100.00)

    def test_list_transactions(self):
        Transaction.objects.create(user=self.user, **self.transaction_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_transaction_detail(self):
        transaction = Transaction.objects.create(user=self.user, **self.transaction_data)
        url = reverse('transaction_detail', kwargs={'pk': transaction.pk})  # Adjust the URL name and parameters as needed
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], 100.00)

    def test_update_transaction(self):
        transaction = Transaction.objects.create(user=self.user, **self.transaction_data)
        url = reverse('transaction_detail', kwargs={'pk': transaction.pk})
        update_data = {
            "date": "2024-10-11",
            "amount": 150.00,
            "transaction_type": "income",
            "payment_method": "mpesa",
            "category": "salary"
        }
        response = self.client.put(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, 150.00)

    def test_delete_transaction(self):
        transaction = Transaction.objects.create(user=self.user, **self.transaction_data)
        url = reverse('transaction_detail', kwargs={'pk': transaction.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Transaction.objects.count(), 0)
