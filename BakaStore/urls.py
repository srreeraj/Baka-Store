"""
URL configuration for BakaStore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings # type: ignore
from django.conf.urls.static import static # type: ignore

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path('BakaAdmin/',include('Admin.urls')),
    path('',include('Users.urls')),
    path('Products/',include('Products.urls')),
    path('Category/',include('Category.urls')),
    path('Cart/',include('Cart.urls')),
    path('Checkout/', include('Checkout.urls')),
    path('Orders/',include('Orders.urls')),
    path('Wallet/',include('Wallet.urls')),
    path('Coupon/',include('Coupons.urls')),
    path('Wishlist/',include('Wishlist.urls')),
    path('Reviews/',include('Reviews.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)