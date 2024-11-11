from django.urls import path # type: ignore
from . import views

urlpatterns = [
    path('',views.home,name='home'),
    path('user-signup/',views.Signup,name='user-signup'),
    path('user-login/',views.Login,name = 'user-login'),
    path('user-logout/',views.Logout,name = 'user-logout'),
    path('verify-otp/',views.verifyOTP,name='verify-otp'),
    path('resend-otp/',views.resend_otp,name='resend-otp'),
    path('admin-customers/',views.admin_users_list,name='customers'),
    path('toggle-customer-status/<int:user_id>/',views.toggle_customer_status, name='toggle-customer-status'),
    path('account/', views.account_details, name='account_details'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('get-address/', views.get_address, name='get_address'),
    path('save-address/', views.save_address, name='save_address'),
    path('delete-address/<int:address_id>/',views.delete_address, name= 'delete_address'),
    path('upload-profile-photo/', views.upload_profile_photo, name='upload_profile_photo'),
    path('forget-password/', views.forget_password, name = 'forget_password'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
]