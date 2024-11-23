from django.shortcuts import render,redirect,get_object_or_404 # type: ignore
from django.contrib.auth import authenticate,login,logout # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from django.views.decorators.cache import never_cache # type: ignore
from .forms import CategoryForm# type: ignore
from Users.models import User # type: ignore
from .models import Category # type: ignore
from Products.models import Product,ProductVariant
from django.utils import timezone # type: ignore
from django.core.cache import cache # type: ignore
from django.http import JsonResponse # type: ignore
from django.contrib import messages # type: ignore
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # type: ignore
from django.urls import reverse # type: ignore
from datetime import timedelta
from Admin.views import admin_required
from django.db.models import Q,Count, F, Case, When, DecimalField  # type: ignore
from decimal import Decimal
from django.template.loader import render_to_string # type: ignore
from django.db import transaction

# Create your views here.

def category(request):
    categories = Category.objects.filter(status='active', is_delete=False).prefetch_related('product_set')
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort')
    search_query = request.GET.get('search')
    now = timezone.now()

    # Base queryset for all variants
    all_variants = ProductVariant.objects.filter(
        product__status='Active',
        product__is_delete=False
    ).exclude(size='Default').select_related('product')

    # Handle search functionality
    if search_query:
        all_variants = all_variants.filter(
            Q(product__name__icontains=search_query) |
            Q(product__category__name__icontains=search_query)
        )
        category_name = f'Search Results for "{search_query}"'
        page_title = f"Search Results - {search_query}"
        breadcrumbs = [
            {'title': 'Shop', 'url': reverse('category')},
            {'title': 'Search Results', 'url': f"{reverse('category')}?search={search_query}"}
        ]
    elif category_id:
        category = get_object_or_404(Category, id=category_id)
        all_variants = all_variants.filter(product__category=category)  # Modified this line
        category_name = category.name
        page_title = f"{category_name} Products"
        breadcrumbs = [
            {'title': 'Shop', 'url': reverse('category')},
            {'title': category_name, 'url': f"{reverse('category')}?category={category_id}"}
        ]
    else:
        category_name = 'All Baka Products!!'
        page_title = "All Products"
        breadcrumbs = [
            {'title': 'Shop', 'url': reverse('category')}
        ]

    # Apply offer calculations
    all_variants = all_variants.annotate(
        product_discount=Case(
            When(
                product__offer_type='percentage',
                product__offer_start_date__lte=now,
                product__offer_end_date__gte=now,
                then=F('price') * (1 - F('product__offer_value') / 100)
            ),
            When(
                product__offer_type='fixed',
                product__offer_start_date__lte=now,
                product__offer_end_date__gte=now,
                then=F('price') - F('product__offer_value')
            ),
            default=F('price'),
            output_field=DecimalField()
        ),
        category_discount=Case(
            When(
                product__category__offer_type='percentage',
                product__category__offer_start_date__lte=now,
                product__category__offer_end_date__gte=now,
                then=F('price') * (1 - F('product__category__offer_value') / 100)
            ),
            When(
                product__category__offer_type='fixed',
                product__category__offer_start_date__lte=now,
                product__category__offer_end_date__gte=now,
                then=F('price') - F('product__category__offer_value')
            ),
            default=F('price'),
            output_field=DecimalField()
        ),
        final_price=Case(
            When(
                product_discount__lt=F('category_discount'),
                then=F('product_discount')
            ),
            default=F('category_discount'),
            output_field=DecimalField()
        )
    )

    # Apply price filter to final_price instead of base price
    if min_price and max_price:
        all_variants = all_variants.filter(final_price__gte=Decimal(min_price), final_price__lte=Decimal(max_price))

    # Apply sorting
    if sort:
        if sort == 'popularity':
            all_variants = all_variants.annotate(order_count=Count('orderitem')).order_by('-order_count')
        elif sort == 'price_low_high':
            all_variants = all_variants.order_by('final_price')  # Changed to sort by final_price
        elif sort == 'price_high_low':
            all_variants = all_variants.order_by('-final_price')  # Changed to sort by final_price
        elif sort == 'new_arrivals':
            thirty_days_ago = timezone.now() - timedelta(days=30)
            all_variants = all_variants.filter(product__created_at__gte=thirty_days_ago).order_by('-product__created_at')
        elif sort == 'name_asc':
            all_variants = all_variants.order_by('product__name', 'size')
        elif sort == 'name_desc':
            all_variants = all_variants.order_by('-product__name', '-size')

    paginator = Paginator(all_variants, 12)
    page = request.GET.get('page')

    try:
        variants = paginator.page(page)
    except PageNotAnInteger:
        variants = paginator.page(1)
    except EmptyPage:
        variants = paginator.page(paginator.num_pages)

    context = {
        'categories': categories,
        'variants': variants,
        'selected_category': category_id,
        'category_name': category_name,
        'page_title': page_title,
        'breadcrumbs': breadcrumbs,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'search_query': search_query,  # Added search_query to context
    }

    return render(request, 'Users/category.html', context)

def new_arrivals(request):
    thirty_days_ago = timezone.now() - timedelta(days=30)
    now = timezone.now()
    
    # Get variants instead of products, excluding Default size
    variants = ProductVariant.objects.filter(
        product__created_at__gte=thirty_days_ago,
        product__status='Active',
        product__is_delete=False,
        status='Active'
    ).exclude(size='Default').select_related('product')

    # Apply the same offer calculations as in category view for consistency
    variants = variants.annotate(
        product_discount=Case(
            When(
                product__offer_type='percentage',
                product__offer_start_date__lte=now,
                product__offer_end_date__gte=now,
                then=F('price') * (1 - F('product__offer_value') / 100)
            ),
            When(
                product__offer_type='fixed',
                product__offer_start_date__lte=now,
                product__offer_end_date__gte=now,
                then=F('price') - F('product__offer_value')
            ),
            default=F('price'),
            output_field=DecimalField()
        ),
        category_discount=Case(
            When(
                product__category__offer_type='percentage',
                product__category__offer_start_date__lte=now,
                product__category__offer_end_date__gte=now,
                then=F('price') * (1 - F('product__category__offer_value') / 100)
            ),
            When(
                product__category__offer_type='fixed',
                product__category__offer_start_date__lte=now,
                product__category__offer_end_date__gte=now,
                then=F('price') - F('product__category__offer_value')
            ),
            default=F('price'),
            output_field=DecimalField()
        ),
        final_price=Case(
            When(
                product_discount__lt=F('category_discount'),
                then=F('product_discount')
            ),
            default=F('category_discount'),
            output_field=DecimalField()
        )
    ).order_by('-product__created_at')

    # Get active categories for the sidebar
    categories = Category.objects.filter(status='active', is_delete=False).prefetch_related('product_set')

    paginator = Paginator(variants, 12)
    page = request.GET.get('page')

    try:
        variants = paginator.page(page)
    except PageNotAnInteger:
        variants = paginator.page(1)
    except EmptyPage:
        variants = paginator.page(paginator.num_pages)

    context = {
        'variants': variants,  # Changed from 'products' to 'variants' to match category template
        'categories': categories,  # Added categories for sidebar
        'category_name': 'New Arrivals',
        'page_title': 'New Arrivals',
        'breadcrumbs': [
            {'title': 'Shop', 'url': reverse('category')},
            {'title': 'New Arrivals', 'url': reverse('new_arrivals')}
        ]
    }

    return render(request, 'Users/category.html', context)



def admin_category_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        category_list = Category.objects.filter(
            Q(name__icontains=search_query),
            is_delete=False
        )
    else:
        category_list = Category.objects.filter(is_delete=False)
    
    paginator = Paginator(category_list, 10)
    page_number = request.GET.get('page')
    
    try:
        categories = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer, deliver first page.
        categories = paginator.page(1)
    except EmptyPage:
        # If the page is out of range, deliver last page of results.
        categories = paginator.page(paginator.num_pages)
    
    context = {
        'categories': categories,
    }
    return render(request, 'Admin/admin_category_list.html', context)


@admin_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category-list')
    else:
        form = CategoryForm()
    return render(request, 'Admin/add_edit_category.html',{'form' : form})

@admin_required
def edit_category(request,pk):
    category = get_object_or_404(Category,pk= pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance= category)
        if form.is_valid():
            form.save()
            return redirect('category-list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'Admin/add_edit_category.html',{'form' : form})

@admin_required
def delete_category(request,pk):
    category = get_object_or_404(Category, pk =pk)
    current_page = request.GET.get('page', 1)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                #Soft delete all related products
                category.product_set.filter(is_delete = False).update(
                    is_delete = True,
                    status = 'inactive'
                )

                # Soft delete all related products variants
                ProductVariant.objects.filter(
                    product__category = category,
                    product__is_delete = True, # only affect variants of deleted products
                    status = 'Active'
                ).update(status = 'Inactive')

                # Finally, soft delete the category
                category.is_delete = True
                category.status ='inactive'
                category.save()

            messages.success(request, f'Category "{category.name}" and its products have been successfully deleted.')
            return redirect(f'{reverse("category-list")}?page={current_page}')
        
        except Exception as e:
            messages.error(request, f'An error occurred while deleting the category: {str(e)}')
            return redirect(f'{reverse("category-list")}?page={current_page}')
    
    # Get related data for confirmation page
    context = {
        'category': category,
        'current_page': current_page,
        'product_count': category.product_set.filter(is_delete=False).count(),
        'variant_count': ProductVariant.objects.filter(
            product__category=category,
            product__is_delete=False,
            status='Active'
        ).count()
    }


        
    return render(request, 'Admin/delete_category.html',context)

