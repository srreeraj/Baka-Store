from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Wishlist
from Products.models import Product,ProductVariant

# Create your views here.

def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user = request.user).prefetch_related('product','product__variants')

    print(f"Wishlist items found : {wishlist_items.count()}")
    for item in wishlist_items:
        print(f" - Product: {item.product.name} (ID : {item.product.id})")

        
    context = {
        'wishlist_items' : wishlist_items
    }
    return render(request, 'Users/wishlist.html', context)

def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id = product_id)
    print(f"Adding product {product.id} to wishlist for user {request.user.id}")
    wishlist_item , created = Wishlist.objects.get_or_create(user = request.user,product =product)

    print(f"Wishlist item created : {created}, User: {request.user.email}, Product: {product.name}")

    if created :
        return JsonResponse({'success' : True, 'message' : 'Product added to wishlist.'})
    else:
        return JsonResponse({'success' : False, 'message' : 'Product already in wishlist'})
    

def remove_from_wishlist(request,wishlist_item_id):
    wishlist_item = get_object_or_404(Wishlist, id = wishlist_item_id, user = request.user)
    wishlist_item.delete()
    return JsonResponse({'success' : True, 'message' : 'Product removed from wishlist'})

