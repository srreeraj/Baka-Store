from django.urls import path
from . import views

urlpatterns = [
    path('mycart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove-from-cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
]
