from django.urls import path
from . import views


urlpatterns = [
    path('product/<int:pk>/',views.product_details,name='product_details'),
    path('admin-products/',views.admin_products,name='product_list'),
    path('add-product/',views.add_product,name='add_products'),
    path('edit-product/<int:pk>/',views.edit_product,name='edit_product'),
    path('delete-product/<int:pk>/,',views.delete_product, name='delete-product'),
]