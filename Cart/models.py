from django.db import models
from Users.models import User
from Products.models import Product, ProductVariant
# Create your models here.

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItems(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True,blank=True)

    def save(self, *args, **kwargs):
        self.discounted_price = self.product.get_discounted_price(self.variant.price)
        super().save(*args,**kwargs)
    
    def total_price(self):
        return self.variant.price * self.quantity
    