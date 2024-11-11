from django.db import models
from Users.models import User
# Create your models here.

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.get_full_name}'s Wallet"
    
class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=30,choices=TRANSACTION_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} for {self.wallet.user.get_full_name}"
