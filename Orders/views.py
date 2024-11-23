from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Order
from Products.models import Product, ProductVariant
from django.db import transaction
import logging
import json
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa  # Import xhtml2pdf


# Create your views here.



def order_history(request):
    orders = Order.objects.filter(user = request.user).order_by('-created_at').prefetch_related('items__product_variant__product')
    context = {
        'orders' : orders
    }
    return render(request, 'Users/order_history.html',context)


def order_list(request):
    query = request.GET.get('q')
    if query:
        orders = Order.objects.filter(
            Q(id__iexact=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        ).order_by('-created_at')
    else:
        orders = Order.objects.all().order_by('-created_at')

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'query': query,
    }

    return render(request, 'Admin/order_list.html', context)

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all().select_related('product_variant__product')

    # Get offers from the products related to the order items
    offers = (
        order_items.values(
            'product_variant__product__offer_type',
            'product_variant__product__offer_value'
        )
        .distinct()
        if order_items.exists()
        else None
    )

    context = {
        'order': order,
        'order_items': order_items,
        'offers': offers,
    }
    return render(request, 'Admin/order_detail.html', context)



def order_detail_users(request,order_id):
    order = get_object_or_404(Order, id = order_id)
    order_items = order.items.all()
    context = {
        'order' : order,
        'order_items' : order_items, 
    }

    return render(request, 'Users/order_detail.html', context)

def update_order_status(request, order_id):
    
    order = get_object_or_404(Order, id=order_id)
    try:
        data = json.loads(request.body)
        status = data.get('status')
        
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICE]
        if status in valid_statuses:
            order.status = status

            if status == 'DELIVERED':
                order.payment_status = 'PAID'

            order.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid Status'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    

def render_to_pdf(template_src, context_dict={}):
    template = render_to_string(template_src, context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'
    pisa_status = pisa.CreatePDF(template, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', content_type='text/plain')
    return response

def generate_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {'order': order}
    return render_to_pdf('Users/invoice.html', context)

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Clear the applied coupon from session to prevent it from affecting future orders
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']

        
    context = {
        'order': order,
    }
    return render(request, 'Users/order_confirmation.html', context)



@require_POST
@login_required
@transaction.atomic
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user = request.user)
    if order.cancel_order():
        message = 'Order cancelled successfully'
        if order.payment_method == 'ONLINE' and order.payment_status == 'REFUNDED':
            message += ' The refund has been credited to your wallet.'
        return  JsonResponse({'success' : True, 'message' : message, 'newStatus' : 'CANCELLED', 'newPaymentStatus' : 'REFUNFDED'})
    return JsonResponse({'success' : False, 'message' : 'Order cannot be cancelled'}, status = 400)

@require_POST
@login_required
@transaction.atomic
def cancel_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.cancel_item(item_id):
        return JsonResponse({'success': True, 'message': 'Item cancelled successfully'})
    return JsonResponse({'success': False, 'message': 'Item cannot be cancelled'}, status=400)

def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.return_order():
        return JsonResponse({
            'message': "Order returned successfully. The refund has been credited to your wallet.",
            'newStatus' : 'RETURNED',
            'newPaymentStatus' : 'REFUNDED'
        })
    else:
        return JsonResponse({'message': "Unable to process the return. Please contact customer support."}, status=400)