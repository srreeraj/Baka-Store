from django.shortcuts import render,redirect
from Cart.models import Cart
from Users.models import Address
from Orders.models import Order, OrderItem, Payment
from Coupons.models import Coupon
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
import razorpay # type: ignore

# Create your views here.

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def checkout(request):
    user = request.user
    try:
        cart = Cart.objects.get(user=user)
        cart_items = cart.items.all()
        
        # Calculate subtotal and total
        cart_subtotal = 0
        cart_total = 0

        for item in cart_items:
            variant = item.variant
            original_price = variant.price
            discounted_price = variant.product.get_discounted_price(original_price)
            item_discounted_price = discounted_price * item.quantity
            
            # Update cart_subtotal and cart_total with the discounted price
            cart_subtotal += item_discounted_price
            cart_total += item_discounted_price
            
            # Save the discounted price in the item object (for use in template)
            item.discounted_price = discounted_price
    except Cart.DoesNotExist:
        cart_items = []
        cart_subtotal = 0
        cart_total = 0
    
    addresses = Address.objects.filter(user =user)

    
    coupon = None
    discount = 0
    
    # Get the applied coupon from the session
    coupon_code = request.session.get('applied_coupon')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon.is_valid() and cart_total >= 5000:
                if coupon.discount_type == 'percentage':
                    discount = (coupon.discount_amount / 100) * cart_total
                else:
                    discount = min(coupon.discount_amount, cart_total)
                cart_total -= discount
        except Coupon.DoesNotExist:
            # Clear invalid coupon from session
            if 'applied_session' in request.session:
                del request.session['applied_session']


    if request.method == 'POST':
        shipping_address_id = request.POST.get('shipping_address')
        payment_method = request.POST.get('payment_method')
        coupon_code = request.POST.get('voucher_code')

        # Validate payment method based on cart total
        if cart_total > 2000 and payment_method != 'ONLINE':
            messages.error(request, 'Orders above ₹2,000 must be paid online.')
            return redirect('checkout')

        shipping_address = Address.objects.get(id = shipping_address_id, user =user)

        for cart_item in cart_items:
            if not cart_item.variant.has_sufficient_stock(cart_item.quantity):
                messages.error(request, f"Not enough stock for {cart_item.variant.product.name} - {cart_item.variant.size}")
                return redirect('checkout')
            
        with transaction.atomic():
            order = Order.objects.create(
                user = user,
                shipping_address = shipping_address,
                billing_address = shipping_address,
                total_amount = cart_total,
                payment_method =payment_method,
            )

            for cart_item in cart_items:
                if cart_item.variant.decrease_stock(cart_item.quantity):
                    OrderItem.objects.create(
                        order = order,
                        product_variant = cart_item.variant,
                        quantity = cart_item.quantity,
                        price = cart_item.variant.price,
                    )
                else:
                    messages.error(request, f"Failed to decrease stock for {cart_item.variant.product.name} - {cart_item.variant.size}")
                    transaction.set_rollback(True)
                    return redirect('checkout')
                
            if coupon:
                order.apply_coupon(coupon)
                # Clear the coupon from session after successful order
                if 'applied_coupon' in request.session:
                    del request.session['applied_coupon']
     
            if payment_method == 'ONLINE':
                # Convert cart_total to paisa (multiply by 100)
                amount_in_paisa = int(cart_total * 100)

                razorpay_order = client.order.create({
                    'amount' : amount_in_paisa,
                    'currency' : 'INR',
                    'payment_capture' : 1,
                })

                payment = Payment.objects.create(
                    order = order,
                    amount = cart_total,
                    razorpay_order_id = razorpay_order['id'],
                    status = 'PENDING',
                )

                context = {
                    'razorpay_order_id' : razorpay_order['id'],
                    'amount' : cart_total,
                    'razorpay_merchent_key' : settings.RAZORPAY_KEY_ID,
                    'razorpay_amount' : int(cart_total * 100),
                    'currency' : 'INR',
                    'callback_url' : 'http://' + request.get_host() + '/razorpay_callback/',
                    'order' : order,
                }
                return render(request, 'Users/razorpay_payment.html', context)
            else:
                if 'applied_coupon' in request.session:
                    del request.session['applied_coupon']

                cart.items.all().delete()
                return redirect('order_confirmation', order_id = order.id) 
    
    context = {
        'user': user,
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'cart_total': cart_total,
        'addresses': addresses,
        'coupon': coupon,
        'discount': discount,
        'allow_cod': cart_total <= 2000 
    }
    return render(request, 'Users/checkout.html', context)

def razorpay_callback(request):
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        params_dict = {
            'razorpay_payment_id' : payment_id,
            'razorpay_order_id' : razorpay_order_id,
            'razorpay_signature' : signature,
        }

        try:
            payment = Payment.objects.get(razorpay_order_id = razorpay_order_id)
            order = payment.order

        except Payment.DoesNotExist:
            return JsonResponse({'success' : 'Failed', 'message' : 'Payment not found'}, status = 400)
        
        try:
            client.utility.verify_payment_signature(params_dict)
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.status = 'PAID'
            payment.save()

            order.payment_status = 'PAID'
            order.save()

            Cart.objects.get(user = order.user).items.all().delete()
            return redirect('order_confirmation', order_id = order.id)
        except Exception as e:
            payment.status = 'FAILED'
            payment.save()
            order.payment_status = 'FAILED'
            order.save()
            return JsonResponse({'status' : 'Failed', 'message' : 'Payment verification failed'})
    return JsonResponse({'status' : 'Failed', 'message' : 'Invalid request'}, status = 400)

def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            cart = Cart.objects.get(user=request.user)
            cart_total = sum(item.total_price() for item in cart.items.all())
            
            if cart_total >= 5000 and coupon.is_valid():
                if coupon.discount_type == 'percentage':
                    discount = (coupon.discount_amount / 100) * cart_total
                else:
                    discount = min(coupon.discount_amount, cart_total)
                
                new_total = cart_total - discount
                
                # Store the applied coupon in the session
                request.session['applied_coupon'] = coupon_code
                
                return JsonResponse({
                    'success': True,
                    'discount': discount,
                    'new_total': new_total,
                    'message': 'Coupon applied successfully!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid coupon or minimum order amount not met.'
                })
        except Coupon.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid coupon code.'
            })
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

