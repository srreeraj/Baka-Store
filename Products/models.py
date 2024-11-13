from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from Category.models import Category
from django.db import transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Product(models.Model):
    name = models.CharField(max_length=40)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image1 = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    status = models.CharField(max_length=50, choices=[('Active','Active'),('Inactive', 'Inactive')])
    is_delete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

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

    def __str__(self):
        return self.name

    def get_total_stock(self):
        return sum(variant.stock for variant in self.variants.all())

    def get_price_range(self):
        prices = [variant.price for variant in self.variants.all()]
        if prices:
            return min(prices), max(prices)
        return None
    
    def get_lowest_price_variant(self):
        return self.variants.order_by('price').first()

    def get_highest_price_variant(self):
        return self.variants.order_by('-price').first()
    
    def get_active_offer(self):
        now = timezone.now()
        if (self.offer_type != 'none' and
            self.offer_start_date <= now <= self.offer_end_date):
            return {
                'type': self.offer_type,
                'value': self.offer_value
            }
        return None

    def get_discounted_price(self, original_price):
        discounted_price = original_price

        # Apply product offer
        if self.offer_type == 'percentage':
            discounted_price *= (1 - self.offer_value / 100)
        elif self.offer_type == 'fixed':
            discounted_price = max(0, discounted_price - self.offer_value)

        # Apply category offer
        if self.category.offer_type == 'percentage':
            discounted_price *= (1 - self.category.offer_value / 100)
        elif self.category.offer_type == 'fixed':
            discounted_price = max(0, discounted_price - self.category.offer_value)

        return round(discounted_price, 2)

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    status = models.CharField(max_length=50, choices=[('Active','Active'),('Inactive', 'Inactive')], default='Active')

    class Meta:
        unique_together = ('product', 'size')
        ordering = ['size']
    
    def __str__(self):
        return f"{self.product.name} - {self.size}"

    def has_sufficient_stock(self, quantity):
        return self.stock >= quantity
    
    def increase_stock(self, quantity):
        self.stock += quantity
        self.save()

    def decrease_stock(self, quantity):
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False
    
    # Products/models.py (add these methods to your ProductVariant class)

def get_average_rating(self):
    """Calculate the average rating for this variant"""
    reviews = self.variant_reviews.all()
    if reviews:
        return round(sum(review.rating for review in reviews) / len(reviews), 1)
    return 0

def get_rating_distribution(self):
    """Get the distribution of ratings for this variant"""
    distribution = {i: 0 for i in range(1, 6)}
    reviews = self.variant_reviews.all()
    total = len(reviews)
    
    for review in reviews:
        distribution[review.rating] += 1
    
    return {
        'distribution': distribution,
        'total': total
    }

def get_verified_reviews_count(self):
    """Get count of verified purchase reviews"""
    return self.variant_reviews.filter(purchase_verified=True).count()

def get_review_count(self):
    """Get total number of reviews"""
    return self.variant_reviews.count()

def user_has_reviewed(self, user):
    """Check if a user has already reviewed this variant"""
    return self.variant_reviews.filter(user=user).exists()

def get_user_review(self, user):
    """Get a user's review for this variant if it exists"""
    return self.variant_reviews.filter(user=user).first()

def can_user_review(self, user):
    """Check if user is eligible to review this variant (has purchased it)"""
    from Orders.models import OrderItem
    return OrderItem.objects.filter(
        order__user=user,
        product_variant=self,
        order__status='Delivered'
    ).exists()

# Add these methods to your ProductVariant model
ProductVariant.get_average_rating = get_average_rating
ProductVariant.get_rating_distribution = get_rating_distribution
ProductVariant.get_verified_reviews_count = get_verified_reviews_count
ProductVariant.get_review_count = get_review_count
ProductVariant.user_has_reviewed = user_has_reviewed
ProductVariant.get_user_review = get_user_review
ProductVariant.can_user_review = can_user_review