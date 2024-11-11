from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.
class Category(models.Model):
    STATUS_CHOICE = (
        ('active','Active'),
        ('inactive','Inactive')
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICE, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_delete = models.BooleanField(default=False)

    OFFER_TYPES = (
        ('none', 'No Offer'),
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPES, default='none')
    offer_value = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    offer_start_date = models.DateTimeField(null=True, blank=True)
    offer_end_date = models.DateTimeField(null=True, blank=True)
    

    class Meta:
        constraints = [
            UniqueConstraint(Lower('name'), name='unique_category_name_case_insensitive')
        ]


    def get_active_offer(self):
        now = timezone.now()
        if (self.offer_type != 'none' and
            self.offer_start_date <= now <= self.offer_end_date):
            return {
                'type': self.offer_type,
                'value': self.offer_value
            }
        return None

    def apply_discount(self, price):
        offer = self.get_active_offer()
        if not offer:
            return price
        
        if offer['type'] == 'percentage':
            discount = price * (offer['value'] / 100)
            return max(price - discount, 0)
        elif offer['type'] == 'fixed':
            return max(price - offer['value'], 0)
        
        return price

    def __str__(self):
        return self.name