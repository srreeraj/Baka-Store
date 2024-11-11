from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import ProductForm, ProductVariantFormSet
from .models import Product, ProductVariant
from Category.models import Category
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Prefetch
from django.contrib import messages
from Admin.views import admin_required

@login_required
@never_cache
def product_details(request, pk):
    product = get_object_or_404(Product, pk=pk)
    variants = product.variants.all().exclude(size='Default')
    selected_variant = variants.first()
    
    # Apply discounts to variants
    discounted_variants = []
    selected_variant_info = None
    for variant in variants:
        original_price = variant.price
        discounted_price = product.get_discounted_price(original_price)
        
        # Apply additional discounts from offers
        if product.offer_type == 'percentage':
            discounted_price *= (1 - product.offer_value / 100)
        elif product.offer_type == 'fixed':
            discounted_price = max(0, discounted_price - product.offer_value)
        
        if product.category.offer_type == 'percentage':
            discounted_price *= (1 - product.category.offer_value / 100)
        elif product.category.offer_type == 'fixed':
            discounted_price = max(0, discounted_price - product.category.offer_value)
        
        discounted_price = round(discounted_price, 2)
        
        variant_info = {
            'variant': variant,
            'original_price': original_price,
            'discounted_price': discounted_price,
            'discount_percentage': round(((original_price - discounted_price) / original_price) * 100, 2) if discounted_price < original_price else 0
        }
        discounted_variants.append(variant_info)
        if variant == selected_variant:
            selected_variant_info = variant_info
    
    active_offer = product.get_active_offer()

    context = {
        'product': product,
        'variants': discounted_variants,
        'active_offer': active_offer,
        'selected_variant': selected_variant,
        'selected_variant_info': selected_variant_info,
    }
    
    return render(request, 'Users/product_detail.html', context)

@admin_required
@never_cache
def admin_products(request):
    search_query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    products_list = Product.objects.filter(is_delete=False).prefetch_related('variants')

    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if category:
        products_list = products_list.filter(category__name=category)

    if status:
        products_list = products_list.filter(status=status)
        

    paginator = Paginator(products_list, 4) 
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category,
        'selected_status': status,
    }
    return render(request, 'Admin/admin_product_list.html', context)

@admin_required
@never_cache
def add_product(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES)
        variant_formset = ProductVariantFormSet(request.POST)
        
        if product_form.is_valid() and variant_formset.is_valid():
            # Save product first
            product = product_form.save(commit=False)
            product.save()
            
            # Save variants
            formset = ProductVariantFormSet(request.POST, instance=product)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Product added successfully!')
                return redirect('product_list') 
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        product_form = ProductForm()
        variant_formset = ProductVariantFormSet()
    
    context = {
        'product_form': product_form,
        'variant_formset': variant_formset,
        'title': 'Add Product'
    }
    return render(request, 'Admin/add_edit_product.html', context)



@login_required
@never_cache
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_form = ProductForm(request.POST, request.FILES, instance=product)
        variant_formset = ProductVariantFormSet(request.POST, instance=product)
        
        if product_form.is_valid() and variant_formset.is_valid():
            product = product_form.save()
            variant_formset.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        product_form = ProductForm(instance=product)
        variant_formset = ProductVariantFormSet(instance=product)
    
    context = {
        'product_form': product_form,
        'variant_formset': variant_formset,
        'title': 'Edit Product',
        'product': product
    }
    return render(request, 'Admin/add_edit_product.html', context)

@login_required
@never_cache
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.is_delete = True
        product.save()    
        return redirect('products')
    return render(request, 'Admin/delete_product.html', {'product': product})