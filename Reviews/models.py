from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from Products.models import Product, ProductVariant
from Users.models import User

# Create models here 

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='product_reviews', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, related_name='variant_reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='user_reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    title = models.CharField(max_length=100, blank=True, null=True)
    comment = models.TextField()
    purchase_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product', 'variant'],
                name='unique_review_per_user_variant'
            )
        ]
        
    def __str__(self):
        return f"{self.user.email}'s review on {self.product.name} - {self.variant.size}"

    def save(self, *args, **kwargs):
        # Check if this is a verified purchase
        from Orders.models import OrderItem  # Import here to avoid circular import
        self.purchase_verified = OrderItem.objects.filter(
            order__user=self.user,
            variant=self.variant,
            order__status='Delivered'  # Only count delivered orders
        ).exists()
        super().save(*args, **kwargs)