from django.urls import path
from . import views

urlpatterns = [
    path('coupons/',views.coupon_list, name='coupons'),
    path('coupons/add', views.add_coupon, name= 'add-coupon'),
    path('coupons/edit/<int:pk>/', views.edit_coupon, name='edit-coupon'),
]