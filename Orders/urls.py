from django.urls import path
from . import views

urlpatterns = [
    path('order-history/', views.order_history, name='order_history'),
    path('order-list-admin/', views.order_list, name='order-list'),
    path('order-detail-admin/<int:order_id>/',views.order_detail, name='order-detail'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update-order-status'),
    path('order-confirmed/<int:order_id>/',views.order_confirmation,name= 'order_confirmation'),
    path('order-cancel/<int:order_id>/cancel/',views.cancel_order, name = 'cancel_order'),
    path('order-detail/<int:order_id>',views.order_detail_users, name = 'order_detail_user'),
    path('order/<int:order_id>/cancel-item/<int:item_id>/', views.cancel_order_item, name='cancel_order_item'),
    path('order/<int:order_id>/return/', views.return_order, name='return_order'),
    path('order/<int:order_id>/invoice/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
]