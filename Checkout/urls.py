from django.urls import path
from . import views

urlpatterns = [
    path('checkout/',views.checkout, name = 'checkout'),
    path('razorpay-callback/', views.razorpay_callback, name='razorpay_callback'),
    path('checkout/apply-coupon/', views.apply_coupon, name='apply_coupon'),
]