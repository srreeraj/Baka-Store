from django.db import models
from django.utils import timezone
from Users.models import User, Address
from Products.models import Product,ProductVariant
from Wallet.models import Wallet,Transaction
from django.db import transaction
from Coupons.models import Coupon
#Create your models here.

class Order(models.Model):
        STATUS_CHOICE = (
                ('PENDING', 'Pending'),
                ('PROCESSING', 'Processing'),
                ('SHIPPED', 'Shipped'),
                ('DELIVERED', 'Delivered'),
                ('CANCELLED', 'Cancelled'),
                ('RETURNED', 'Returned'),
        )

        PAYMENT_METHOD_CHOICE = (
            ('ONLINE','Online Payment'),
            ('COD', 'Cash On Delivery'),
        )

        PAYMENT_STATUS_CHOICE = (
            ('PENDING', 'Pending'),
            ('PAID', 'Paid'),
            ('FAILED', 'Failed'),
            ('REFUNDED' ,'Refunded')
        )

        user = models.ForeignKey(User, on_delete= models.CASCADE, related_name='orders')
        shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
        billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, related_name='billing_orders')
        created_at = models.DateTimeField(auto_now_add=True)
        total_amount = models.DecimalField(max_digits=10, decimal_places=2)
        status = models.CharField(max_length=20, choices=STATUS_CHOICE, default='PENDING')
        payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICE, default='COD')
        razorpay_order_id = models.CharField(max_length=100, blank=True, null= True)
        razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
        razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
        payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICE, default='PENDING')
        coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
        discount = models.DecimalField(max_digits=10, decimal_places=2, default= 0)

        def __str__(self):
            return f"Order {self.id} by {self.user.get_full_name()}"
        
        def recalculate_totals(self):
            self.total_amount = sum(item.get_total() for item in self.items.all())
            self.total_amount += self.shipping_cost  # Include shipping cost if applicable
            self.save()

        def cancel_item(self, item_id):
            try:
                item = self.items.get(id = item_id)
                if self.status == 'PENDING' and item.status == 'ACTIVE':
                    item.product_variant.product.increase_stock(item.quantity)
                    item.status = 'CANCELLED'
                    item.saved()
                    self.recalculate_totals()
                    return True
                return False
            except OrderItem.DoesNotExist:
                return False
               
        def cancel_order(self):
            if self.status == 'PENDING':
                #Change order status to Cancelled
                self.status = 'CANCELLED'

                # Refund if the payment method was online and payment status is paid
                if self.payment_method == 'ONLINE' and self.payment_status == 'PAID':
                    wallet, created = Wallet.objects.get_or_create(user = self.user)

                    Transaction.objects.create(
                        wallet = wallet,
                        amount = self.total_amount,
                        description = f"Refunded for cancelled order #{self.id}"
                    )

                    wallet.balance += self.total_amount
                    wallet.save()

                    self.payment_status = 'REFUNDED'

                for item in self.items.all():
                    item.product_variant.increase_stock(item.quantity)

                self.save()
                return True
            return False
        
        def cancel_item(self,item_id):
            try:
                item = self.items.get(id = item_id)
                if self.status == 'PENDING':
                     item.product.increase_stock(item.quantity)
                     item.status = 'CANCELLED'
                     item.save()
                     self.recalculate_totals()
                     return True
                return False
            
            except OrderItem.DoesNotExist:
                return False
            
        def return_order(self):
            if self.status == 'DELIVERED' and self.payment_status == 'PAID':
                # Change the order status to RETURNED
                self.status = 'RETURNED'
                # Change the payment status to refunded
                self.payment_status = 'REFUNDED'
                self.save()

                # Increase the stock for each item
                for item in self.items.all():
                    item.product_variant.increase_stock(item.quantity)

                #Refund to wallet
                wallet, created = Wallet.objects.get_or_create(user = self.user)
                Transaction.objects.create(
                    wallet = wallet,
                    amount = self.total_amount,
                    description = f"Refund for returned order #{self.id}"
                )
                wallet.balance += self.total_amount
                wallet.save()

                return True
            return True
        
        def apply_coupon(self,coupon):
            if self.total_amount >= 5000 and coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    self.discount = (coupon.discount_amount / 100) * self.total_amount
                else:
                    self.discount = coupon.discount_amount
                self.total_amount -= self.discount
                self.coupon = coupon
                self.save()
                return True
            return False
        
        def recalculate_totals(self):
            self.total_amount = sum(item.total_price() for item in self.items.all())
            self.save()
                      
        
        class Meta:
                ordering = ['-created_at']


class OrderItem(models.Model):
        order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
        product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
        quantity = models.PositiveIntegerField(default=1)
        price = models.DecimalField(max_digits=10, decimal_places= 2)
        status = models.CharField(max_length=20, choices=Order.STATUS_CHOICE, default='PENDING')


        def __str__(self):
                return f"{self.quantity} of {self.product_variant.product.name} in Order {self.order.id}"
        
        def total_price(self):
            return self.quantity * self.price
        
        def save(self, *args, **kwargs):
            if not self.pk:
                self.product_variant.decrease_stock(self.quantity)
            super().save(*args, **kwargs)

        def delete(self, *args, **kwargs):
             self.product_variant.increase_stock(self.quantity)
             super().delete(*args, **kwargs)

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Order.PAYMENT_STATUS_CHOICE, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __Str__(self):
        return f"Payment for Order {self.order.id}"