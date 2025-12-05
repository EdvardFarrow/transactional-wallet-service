from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    
    def __str__(self):
        return f"Wallet {self.user.username} ({self.balance})"

class Transaction(models.Model):
    sender = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='sent_transactions')
    receiver = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='received_transactions')
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    fee = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, default='success')
    created_at = models.DateTimeField(auto_now_add=True)