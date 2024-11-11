from django.shortcuts import render, get_object_or_404,redirect
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItems
from Products.models import Product, ProductVariant
from django.http import JsonResponse
from django.contrib import messages 
# Create your views here.

def cart(request):
    try:
        cart = Cart.objects.get(user = request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart_items = []

    for item in cart_items:
        item.discounted_price = item.product.get_discounted_price(item.variant.price)
        item.discounted_total = item.discounted_price * item.quantity
    
    total = sum(item.discounted_total for item in cart_items)

    context = {
        'cart_items' : cart_items,
        'total' : total
    }
    return render(request,'Users/cart.html',context)

def add_to_cart(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    
    product = get_object_or_404(Product, id=product_id)
    variant_id = request.POST.get('variant_id')

    try:
        variant = ProductVariant.objects.get(id=variant_id, product=product)
    except ProductVariant.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid product variant'}, status=400)
    
    if variant.stock < 1:
        return JsonResponse({'success': False, 'message': 'Product is out of stock'}, status=400)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItems.objects.get_or_create(cart=cart, product=product, variant=variant)

    if item_created:
        cart_item.quantity = 1
    else:
        cart_item.quantity += 1

    if cart_item.quantity > variant.stock:
        return JsonResponse({'success': False, 'message': 'Cannot add more of this item'}, status=400)
    
    cart_item.save()
    return JsonResponse({'success': True, 'message': f'{product.name} - {variant.size} added to your cart'})



def remove_from_cart(request,item_id):
    cart_item = get_object_or_404(CartItems, id = item_id, cart__user = request.user)
    cart_item.delete()
    return redirect('cart')

def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItems, id = item_id, cart__user = request.user)
    quantity = int(request.POST.get('quantity', 1))

    if quantity > cart_item.variant.stock:
        return JsonResponse({'error' : 'Quantity exceeds available stock'}, status = 400)
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()

    cart = cart_item.cart
    cart_total = sum(item.total_price() for item in cart.items.all())

    return JsonResponse({
        'success' : True,
        'item_total' : float(cart_item.total_price()),
        'cart_total' : float(cart_total)
    })