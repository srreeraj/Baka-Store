from django.db import models
from django.utils import timezone

# Create your models here.

class Coupon(models.Model):

    DISOUNT_TYPE_CHOICE = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount')
    ]

    code = models.CharField(max_length=30, unique=True)
    description = models.TextField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_type = models.CharField(max_length=40, choices=DISOUNT_TYPE_CHOICE)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_uses = models.IntegerField(null=True, blank=True)
    current_uses = models.IntegerField(default=0)

    def __str__(self):
        return self.code
    
    def is_valid(self):
        now = timezone.now()
        is_active = self.is_active
        not_expired = self.valid_from <= now <= self.valid_to
        not_max_used = self.max_uses is None or self.current_uses < self.max_uses
        return is_active and not_expired and not_max_used
    
    def apply_discount(self, amount):
        if self.discount_type == 'percentage':
            return amount * (self.discount_amount / 100)
        else:
            return min(self.discount_amount, amount)
        
    def use(self):
        if self.max_uses is None or self.current_uses < self.max_uses:
            self.current_uses += 1
            self.save()
            return True
        return False
    