from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Review
from .forms import ReviewForm
from Products.models import Product, ProductVariant
from Orders.models import OrderItem
# Create your views here.

@login_required
@require_POST
def create_review(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
    
    # Check if user has purchased this variant
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        variant=variant,
        order__status='Delivered'
    ).exists()
    
    if not has_purchased:
        messages.error(request, "You can only review products you have purchased.")
        return redirect('product_details', pk=product_id)
    
    # Check if user already reviewed this variant
    existing_review = Review.objects.filter(
        user=request.user, 
        product=product,
        variant=variant
    ).first()
    
    if existing_review:
        form = ReviewForm(request.POST, instance=existing_review)
        success_message = "Your review has been updated successfully!"
    else:
        form = ReviewForm(request.POST)
        success_message = "Your review has been submitted successfully!"
    
    if form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.variant = variant
        review.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': success_message,
                'review': {
                    'rating': review.rating,
                    'title': review.title,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'verified_purchase': review.purchase_verified,
                }
            })
        
        messages.success(request, success_message)
        return redirect('product_details', pk=product_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)
    
    messages.error(request, "There was an error with your review. Please try again.")
    return redirect('product_details', pk=product_id)

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_id = review.product.id
    review.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Review deleted successfully!'
        })
    
    messages.success(request, "Your review has been deleted successfully!")
    return redirect('product_details', pk=product_id)