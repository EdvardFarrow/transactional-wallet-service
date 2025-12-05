from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from core.models import Wallet
from decimal import Decimal

class TransferTests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user(username='alice', password='password')
        self.bob = User.objects.create_user(username='bob', password='password')
        
        self.alice_wallet = Wallet.objects.create(user=self.alice, balance=Decimal('1000.00'))
        self.bob_wallet = Wallet.objects.create(user=self.bob, balance=Decimal('0.00'))
        
        self.url = reverse('transfer') 

    def test_successful_transfer(self):
        """Regular transaction"""
        self.client.force_authenticate(user=self.alice)
        data = {'to_user': 'bob', 'amount': '100.00'}
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.alice_wallet.refresh_from_db()
        self.bob_wallet.refresh_from_db()
        
        self.assertEqual(self.alice_wallet.balance, Decimal('900.00'))
        self.assertEqual(self.bob_wallet.balance, Decimal('100.00'))

    def test_insufficient_funds(self):
        """Insufficient funds"""
        self.client.force_authenticate(user=self.alice)
        data = {'to_user': 'bob', 'amount': '2000.00'} 
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.alice_wallet.refresh_from_db()
        self.assertEqual(self.alice_wallet.balance, Decimal('1000.00'))

    def test_transfer_with_fee(self):
        """Transaction with comission (>1000) - Fee on top"""
        self.alice_wallet.balance = Decimal('5000.00')
        self.alice_wallet.save()
        
        self.client.force_authenticate(user=self.alice)
        data = {'to_user': 'bob', 'amount': '2000.00'}
        
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.alice_wallet.refresh_from_db()
        self.bob_wallet.refresh_from_db()
        
        self.assertEqual(self.alice_wallet.balance, Decimal('2800.00'))
        
        self.assertEqual(self.bob_wallet.balance, Decimal('2000.00'))
        
        admin_wallet = Wallet.objects.get(user__username='admin')
        self.assertEqual(admin_wallet.balance, Decimal('200.00'))

    def test_cannot_transfer_to_self(self):
        self.client.force_authenticate(user=self.alice)
        data = {'to_user': 'alice', 'amount': '100.00'}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)