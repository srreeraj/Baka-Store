from django.urls import path
from . import views


urlpatterns = [
    path('category/',views.category,name = 'category'),
    path('new-arrivals',views.new_arrivals, name= 'new_arrivals'),
    path('admin-category/',views.admin_category_list,name='category-list'),
    path('category/add',views.add_category,name='add-category'),
    path('category/edit/<int:pk>/',views.edit_category,name = 'edit-category'),
    path('category/delete/<int:pk>/',views.delete_category,name='delete-category'),
]