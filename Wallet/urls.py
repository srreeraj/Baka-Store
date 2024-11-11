from django.urls import path
from . import views

urlpatterns = [
    path('wallet/', views.wallet_view,name='wallet'),
    path('wallet/add-funds/', views.add_funds, name= 'add_funds'),
    path('wallet/withdraw-funds/', views.withdraw_funds, name='withdraw_funds'),
]